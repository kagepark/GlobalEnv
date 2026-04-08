class Environment:
    """이름별 글로벌 싱글톤 딕셔너리 클래스
    로보프레임워크와 일반 파이썬에서 공유하여 사용 가능
    """
    _instances = {} # name → instance (싱글톤 관리)

    def __new__(cls, name='settings', **initial_data):
        if not name or not isinstance(name, str):
            name = 'settings'

        if name not in cls._instances:
            instance = super().__new__(cls)
            instance._name = name
            instance.settings = {}
            cls._instances[name] = instance

        instance = cls._instances[name]
        if initial_data:
            instance.update(**initial_data)
        return instance

    def name(self):
        return self._name

    def reset(self, **kwargs):
        self.settings = {}
        if kwargs:
            self.update(**kwargs)

    def _resolve_path(self, data, key, path=False):
        if not (isinstance(path, str) and len(path) == 1 and isinstance(key, str) and key):
            return data, key

        parts = key.split(path)
        if len(parts) <= 1:
            return data, key

        for p in parts[:-1]:
            if not p: continue
            if isinstance(data, dict) and p in data and isinstance(data[p], dict):
                data = data[p]
            else:
                return None, None
        return data, parts[-1]

    def get(self, key=None, default=None, all_key=False, split_symbol=',', path=False):
        data, key = self._resolve_path(self.settings, key, path)
        if data is None or not isinstance(data, dict):
            return default if not all_key else [default]

        if key is None:
            return data

        if isinstance(key, str) and split_symbol in key:
            key = key.split(split_symbol)

        if isinstance(key, (list, tuple)):
            results = [data.get(k, default) for k in key]
            return results if all_key else next((v for v in results if v != default), default)
        return data.get(key, default)

    def set(self, key=None, value=None, path=False, merge=False, **kwargs):
        """
        key, value로 설정
        merge=True 이면 value가 dict일 경우 기존 값과 merge 함
        """
        data, key = self._resolve_path(self.settings, key, path)
        if data is None or not isinstance(data, dict):
            return False

        if key is not None and value is not None:
            if merge and isinstance(value, dict) and isinstance(data.get(key), dict):
                # 중첩 merge
                data[key].update(value)          # 얕은 merge
                # 깊은 merge를 원하면 deep_update 호출 가능
            else:
                data[key] = value

        # **kwargs 처리
        for k, v in kwargs.items():
            data[k] = v

        return True

    def update(self, *dicts, level=-1, **kwargs):
        """deep merge"""
        def deep_merge(target, source, curr_level=0):
            if level != -1 and curr_level >= level:
                target.update(source)
                return
            for k, v in source.items():
                if k in target and isinstance(target[k], dict) and isinstance(v, dict):
                    deep_merge(target[k], v, curr_level + 1)
                else:
                    target[k] = v

        for d in dicts:
            if isinstance(d, dict):
                deep_merge(self.settings, d)
        if kwargs:
            deep_merge(self.settings, kwargs)
        return True

    # dict 호환 메서드들
    def __iter__(self):
        return iter(self.settings)

    def keys(self):
        return self.settings.keys()

    def values(self):
        return self.settings.values()

    def items(self):
        return self.settings.items()

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.set(key, value)

    def __repr__(self):
        return f"Environment(name='{self._name}', settings={self.settings})"
