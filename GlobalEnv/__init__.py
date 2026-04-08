import os

class Environment:
    _instances = {}
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

    def pop(self,name,default=None):
        if name in self.settings:
            return self.settings.pop(name)
        return default

    def reset(self, **kwargs):
        self.settings = {}
        if kwargs:
            self.update(**kwargs)

    def _resolve_path(self, data, key, path=False):
        moved=[]
        if not (isinstance(path, str) and len(path) == 1 and isinstance(key, str) and key):
            return data, key, moved
        parts = key.split(path)
        if len(parts) <= 1:
            return data, key, moved
        for p in parts[:-1]:
            if not p: continue
            if isinstance(data, dict) and p in data and isinstance(data[p], dict):
                moved.append(p)
                data = data[p]
            else:
                return None, None, moved
        return data, parts[-1], moved

    def get(self, key=None, default=None, all_key=False, split_symbol=',', path=False):
        data, key, dummy = self._resolve_path(self.settings, key, path)
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
        data, key, dummy = self._resolve_path(self.settings, key, path)
        if data is None or not isinstance(data, dict):
            return False
        if key is not None and value is not None:
            if merge and isinstance(value, dict) and isinstance(data.get(key), dict):
                data[key].update(value)
            else:
                data[key] = value
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

    def exists(self, key=None, default=False, all_key=False,split_symbol=',',rv={None},path=False):
        # return : rv is bool then return True/False
        #          rv is {None} then return key/default
        # Check being key or not
        #if path: all_key=True
        data, key, cur = self._resolve_path(self.settings, key, path)
        if isinstance(data,dict):
            if not key:
                if data: # any data then True when no key
                    if rv in [bool,'bool']:
                        return True
                    else:
                        return data
            else:
                if isinstance(key,str) and split_symbol in key:
                    key=key.split(',')
                if isinstance(key,(list,tuple)):
                    out=[]
                    for i in key:
                        if all_key:
                            if i in data:
                                if rv in [bool,'bool']:
                                    out.append(True)
                                else:
                                    out.append(os.path.join(*cur,i))
                            else:
                                if rv in [bool,'bool']:
                                    out.append(False)
                                else:
                                    out.append(default)
                        else:
                            if i in data:
                                #first any key found then return
                                if rv in [bool,'bool']:
                                    return True
                                else:
                                    return os.path.join(*cur,i)
                    if all_key:
                        #for all_key=True
                        return out
                    else:
                        #not found case when all_key=False
                        if rv in [bool,'bool']: #Not found
                            return False
                        return default
                else:
                    if key in data:
                        if rv in [bool,'bool']:
                            return True
                        else:
                            if all_key:
                                return [os.path.join(*cur,key)]
                            else:
                                return os.path.join(*cur,key)
        if all_key:
            if rv in [bool,'bool']:
                return [False]
            return [default]
        else:
            if rv in [bool,'bool']:
                return False
            return default

    def remove(self, key, split_symbol=',',path=False):  # Removed default parameter as it's not used
        for k in self.exists(key,all_key=True,default=False,split_symbol=split_symbol,path=path):
            if k is not False:
                data, key, dummy = self._resolve_path(self.settings, k, path)
                del data[key]

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
