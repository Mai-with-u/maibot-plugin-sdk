"""旧版 utils 模块 (兼容层)"""

import warnings


class ManifestValidator:
    """旧版 ManifestValidator 占位"""

    def __init__(self, *args, **kwargs):
        warnings.warn("ManifestValidator 已弃用，请使用新版 _manifest.json 校验器", DeprecationWarning, stacklevel=2)

    def validate(self, *args, **kwargs):
        return True

    @property
    def errors(self):
        return []
