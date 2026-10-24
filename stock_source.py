# SPDX-License-Identifier: Apache-2.0
"""Read-only LP/ext4 access and pinned extraction checks, independent of mounted runtime."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import struct

DEVICE = Path(__file__).resolve().parent


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while chunk := stream.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def plan():
    return json.loads((DEVICE / 'configs' / 'blob-plan.json').read_text(encoding='utf-8'))


def proof():
    return json.loads((DEVICE / 'configs' / 'stock-source.json').read_text(encoding='utf-8'))


class LpPartition:
    def __init__(self, super_path, metadata_view, partition, expected_metadata_sha256):
        self.stream = Path(super_path).open('rb')
        self.position = 0
        self.stream.seek(4096)
        geometry = self.stream.read(4096)
        if struct.unpack_from('<I', geometry)[0] != 0x616c4467:
            raise ValueError('Expected the audited raw super, not an Android sparse image')
        maximum, slots = struct.unpack_from('<II', geometry, 40)
        if not 0 <= metadata_view < slots:
            raise ValueError('LP view outside geometry')
        self.stream.seek(12288 + metadata_view * maximum)
        metadata = self.stream.read(maximum)
        header_size = struct.unpack_from('<I', metadata, 8)[0]
        table_size = struct.unpack_from('<I', metadata, 44)[0]
        digest = hashlib.sha256(metadata[:header_size + table_size]).hexdigest()
        if digest != expected_metadata_sha256:
            raise ValueError('LP metadata differs from the audited .680 source')
        tables = metadata[header_size:header_size + table_size]

        def table(index):
            offset, count, size = struct.unpack_from('<III', metadata, 80 + index * 12)
            return [tables[offset + i * size:offset + (i + 1) * size] for i in range(count)]

        partitions, extents = table(0), table(1)
        entry = next((p for p in partitions if p[:36].split(b'\0')[0].decode() == partition), None)
        if entry is None:
            raise ValueError('Missing audited logical partition: ' + partition)
        _, first, count, _ = struct.unpack_from('<IIII', entry, 36)
        self.extents = []
        logical = 0
        for entry in extents[first:first + count]:
            sectors, kind, target, source = struct.unpack('<QIQI', entry)
            if kind != 0 or source != 0:
                raise ValueError('This audited source requires only linear extents on super')
            length = sectors * 512
            self.extents.append((logical, logical + length, target * 512))
            logical += length
        self.size = logical

    def seek(self, offset):
        if not 0 <= offset <= self.size:
            raise ValueError('LP seek outside partition')
        self.position = offset

    def read(self, count):
        count = min(count, self.size - self.position)
        output = bytearray()
        while count:
            match = next((e for e in self.extents if e[0] <= self.position < e[1]), None)
            if match is None:
                raise ValueError('LP mapping contains a hole')
            start, end, physical = match
            length = min(count, end - self.position)
            self.stream.seek(physical + self.position - start)
            data = self.stream.read(length)
            if len(data) != length:
                raise ValueError('Truncated super')
            output.extend(data)
            self.position += length
            count -= length
        return bytes(output)

    def close(self):
        self.stream.close()


class Ext4:
    def __init__(self, stream):
        self.stream = stream
        sb = self.read_at(1024, 1024)
        if sb[56:58] != b'\x53\xef':
            raise ValueError('Expected audited ext4')
        self.block_size = 1024 << struct.unpack_from('<I', sb, 24)[0]
        self.inodes_per_group = struct.unpack_from('<I', sb, 40)[0]
        self.inode_size = struct.unpack_from('<H', sb, 88)[0]
        self.descriptor_size = max(32, struct.unpack_from('<H', sb, 254)[0])
        self.gdt = (2 if self.block_size == 1024 else 1) * self.block_size
        self.directories = {}

    def read_at(self, offset, length):
        self.stream.seek(offset)
        data = self.stream.read(length)
        if len(data) != length:
            raise ValueError('Truncated ext4 read')
        return data

    def inode(self, number):
        group, index = divmod(number - 1, self.inodes_per_group)
        descriptor = self.read_at(self.gdt + group * self.descriptor_size, self.descriptor_size)
        table = struct.unpack_from('<I', descriptor, 8)[0]
        if self.descriptor_size >= 64:
            table |= struct.unpack_from('<I', descriptor, 40)[0] << 32
        return self.read_at(table * self.block_size + index * self.inode_size, self.inode_size)

    def content(self, number, required_type=0x8000):
        inode = self.inode(number)
        if struct.unpack_from('<H', inode)[0] & 0xf000 != required_type:
            raise ValueError('Expected regular file or directory; no implicit symlink following')
        size = struct.unpack_from('<I', inode, 4)[0] | struct.unpack_from('<I', inode, 108)[0] << 32
        if size > 1024 * 1024 * 1024:
            raise ValueError('File exceeds inspection limit')
        if not struct.unpack_from('<I', inode, 32)[0] & 0x80000:
            raise ValueError('Expected extents-based ext4 inode')
        output = bytearray(size)

        def walk(node):
            magic, count, _, depth, _ = struct.unpack_from('<HHHHI', node)
            if magic != 0xf30a:
                raise ValueError('Invalid ext4 extent header')
            for i in range(count):
                entry = node[12 + i * 12:24 + i * 12]
                if depth:
                    _, low, high, _ = struct.unpack('<IIHH', entry)
                    walk(self.read_at(((high << 32) | low) * self.block_size, self.block_size))
                else:
                    logical, length, high, low = struct.unpack('<IHHI', entry)
                    zero = length > 32768
                    length = (length - 32768 if zero else length) * self.block_size
                    logical *= self.block_size
                    length = min(length, size - logical)
                    if length > 0 and not zero:
                        output[logical:logical + length] = self.read_at(((high << 32) | low) * self.block_size, length)
        walk(inode[40:100])
        return bytes(output)

    def resolve(self, relative_path):
        parts = PurePosixPath(relative_path)
        if parts.is_absolute() or '..' in parts.parts:
            raise ValueError('Unsafe relative source path')
        inode = 2
        for part in parts.parts:
            if inode not in self.directories:
                directory = self.content(inode, 0x4000)
                entries = {}
                position = 0
                while position + 8 <= len(directory):
                    number, length, name_size, _ = struct.unpack_from('<IHBB', directory, position)
                    if length < 8 or position + length > len(directory):
                        raise ValueError('Invalid ext4 directory record')
                    if number:
                        name = directory[position + 8:position + 8 + name_size].decode('utf-8')
                        entries[name] = number
                    position += length
                self.directories[inode] = entries
            inode = self.directories[inode].get(part)
            if inode is None:
                raise ValueError('File not present in audited partition: ' + relative_path)
        return inode


def verify_files(base):
    for entry in plan()['files']:
        file = Path(base) / entry['path']
        if file.is_symlink() or not file.is_file() or sha256_file(file) != entry['sha256']:
            raise ValueError('Missing or changed pinned blob: ' + str(file))


def verify_stage(stage):
    receipt = json.loads((Path(stage) / 'khaje-source-receipt.json').read_text(encoding='utf-8'))
    expected = proof()
    if receipt.get('super_sha256') != expected['original_images']['super.img']['sha256']:
        raise ValueError('Stage is not from the audited stock .680 super')
    if receipt.get('blob_plan_sha256') != sha256_file(DEVICE / 'configs/blob-plan.json'):
        raise ValueError('Stage was prepared for a different blob selection')
    verify_files(stage)


def verify_vendor(proprietary):
    verify_files(proprietary)
