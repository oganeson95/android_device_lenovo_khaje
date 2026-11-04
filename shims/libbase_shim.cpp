#include <string>
#include <string_view>

#include <android-base/strings.h>

namespace android::base {

std::string Trim(const std::string& str) {
    return android::base::Trim(std::string_view(str));
}

} // namespace android::base
