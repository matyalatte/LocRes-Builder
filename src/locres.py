import crc
import cityhash
from io_util import *

class Entry:
    def __init__(self, key, value_id, key_hash=None, value=None, value_hash=None):
        self.key_hash = key_hash
        self.key = key
        self.value_hash = value_hash
        self.value_id = value_id
        self.value = value

    def read(f):
        key_hash = read_uint32(f) #key hash (cityhash64)
        key = read_str(f)
        value_hash = read_uint32(f) #value hash (crc)
        value_id = read_uint32(f)
        return Entry(key, value_id, key_hash=key_hash, value_hash=value_hash)

    def write(self, f):
        write_uint32(f, self.key_hash)
        write_str(f, self.key)
        write_uint32(f, self.value_hash)
        write_uint32(f, self.value_id)

    def cal_hash(self):
        self.key_hash = cityhash.string_cityhash(self.key)
        self.value_hash = crc.string_crc32(self.value)
        
    def set_value(self, values):
        self.value = values[self.value_id].str

    def get_values(self, values, raw_values):
        if self.value in raw_values:
            i = raw_values.index(self.value)
            self.value_id=i
            values[i].count+=1
            return
        self.value_id=len(values)
        values.append(Value(self.value))
        raw_values.append(self.value)

class Namespace:
    def __init__(self, namespace, entries, namespace_hash=0):
        self.namespace_hash = namespace_hash
        self.namespace = namespace
        self.entries = entries

    def read(f):
        namespace_hash = read_uint32(f) #namespace hash (cityhash64)
        namespace = read_str(f)
        entries = read_array(f, Entry.read)
        return Namespace(namespace, entries, namespace_hash=namespace_hash)
    
    def write(self, f):
        write_uint32(f, self.namespace_hash)
        write_str(f, self.namespace)
        write_array(f, self.entries, with_length=True)

    def len(self):
        return len(self.entries)
    
    def to_json(self):
        return {entry.key: entry.value for entry in self.entries}
    
    def to_json_with_lang(self, lang):
        return {entry.key: {lang: entry.value} for entry in self.entries}

    def from_json(self, resource_json, lang):
        self.entries = []
        for key in resource_json:
            res = resource_json[key]
            if lang not in res:
                value = None
            else:
                value = res[lang]
            if value is not None:
                key_hash = res['key_hash']
                value_hash = res['value_hash']
                self.entries.append(Entry(key, 0, key_hash=key_hash, value=value, value_hash=value_hash))

    def cal_hash(self):
        self.namespace_hash = cityhash.string_cityhash(self.namespace)

    def set_values(self, values):
        list(map(lambda x: x.set_value(values), self.entries))

    def get_values(self, values, hashes):
        list(map(lambda x: x.get_values(values, hashes), self.entries))

class Value:
    def __init__(self, str, count=1):
        self.str = str
        self.count = count

    def read(f):
        str = read_str(f)
        count = read_uint32(f) #count (how many keys refer to the string)
        return Value(str, count=count)

    def write(self, f):
        write_str(f, self.str)
        write_uint32(f, self.count)

class LocRes:
    MAGIC_GUID =b'\x0E\x14\x74\x75\x67\x4A\x03\xFC\x4A\x15\x90\x9D\xC3\x37\x7F\x1B'

    def __init__(self, version, namespaces):
        self.version = version
        self.namespaces = namespaces

    def load(file):
        print('Loading {}...'.format(file))
        with open(file, 'rb') as f:
            check(f.read(16), LocRes.MAGIC_GUID, msg='Not localization resource.')
            version=read_uint8(f)
            check(version, 3, msg='Unsupported locres version. ({})'.format(version))
            f.seek(8, 1) #offset to values
            f.seek(4, 1) #key count
            namespaces = read_array(f, Namespace.read)
            values = read_array(f, Value.read)
            list(map(lambda x: x.set_values(values), namespaces))
        locres = LocRes(version, namespaces)
        return locres

    def print(self):
        for ns in self.namespaces:
            print('  {}: {}'.format(ns.namespace, ns.len()))

    def save(self, file):
        list(map(lambda x: x.cal_hash(), self.namespaces))

        values = []
        raw_values = []
        for n in self.namespaces:
            n.get_values(values, raw_values)

        print('Saving {}...'.format(file))
        with open(file, 'wb') as f:
            f.write(LocRes.MAGIC_GUID)
            write_uint8(f, self.version)
            offset = f.tell()
            f.seek(4, 1)
            write_uint32(f, 0)
            key_count = sum([ns.len() for ns in self.namespaces])
            write_uint32(f, key_count)
            write_array(f, self.namespaces, with_length=True)
            value_offset = f.tell()
            write_array(f, values, with_length=True)
            f.seek(offset)
            write_uint32(f,value_offset)

    def to_json(self):
        return {ns.namespace: ns.to_json() for ns in self.namespaces}

    def to_json_with_lang(self, lang):
        return {ns.namespace: ns.to_json_with_lang(lang) for ns in self.namespaces}

    def json_to_locres(res_version, resource_json, lang):
        locres = LocRes(res_version, [])
        for ns in resource_json:
            namespace = Namespace(ns, None)
            namespace.from_json(resource_json[ns], lang)
            if namespace.len()>0:
                locres.namespaces.append(namespace)
        return locres

class LocMeta:
    MAGIC_GUID = b'\x4F\xEE\x4C\xA1\x68\x48\x55\x83\x6C\x4C\x46\xBD\x70\xDA\x50\x7C'

    def __init__(self, version, main_lang, main_file, local_languages):
        self.version = version
        self.main_lang = main_lang
        self.main_file = main_file
        self.local_languages = local_languages
        self.resource_name = os.path.basename(main_file).split('.')[0]

    def load(file):
        print('Loading {}...'.format(file))
        with open(file, 'rb') as f:
            check(f.read(16), LocMeta.MAGIC_GUID, msg='Not localization resource.')
            version=read_uint8(f)
            if version not in [0, 1]:
                raise RuntimeError('Unsupported locmeta version. ({})'.format(version))
            main_lang = read_str(f)
            main_file = read_str(f)
            if version==1:
                local_languages = read_str_array(f)
                local_languages.remove(main_lang)
            else:
                local_languages = None
        print('Main language: {}'.format(main_lang))
        print('Main resource: {}'.format(main_file))
        return LocMeta(version, main_lang, main_file, local_languages)

    def save(self, file):
        print('Saving {}...'.format(file))
        with open(file, 'wb') as f:
            f.write(LocMeta.MAGIC_GUID)
            write_uint8(f, self.version)
            write_str(f, self.main_lang)
            write_str(f, self.main_file.replace('\\', '/'))
            if self.version==1:
                languages = self.local_languages+[self.main_lang]
                write_str_array(f, sorted(list(set(languages))), with_length=True)

    def to_json(self):
        return {
            'meta_version': self.version,
            'resource_name': self.resource_name,
            'main_language': self.main_lang
        }

class LocalizationResources:
    def __init__(self, meta, langs, resources):
        self.meta = meta
        self.langs = langs
        self.resources = resources
        
        main_id = self.langs.index(self.meta.main_lang)
        main_language = self.langs.pop(main_id)
        self.main_res = self.resources.pop(main_id)

        #print entry count for each language
        print(main_language)
        self.main_res.print()
        for lang, res in zip(langs, resources):
            print(lang)
            res.print()

    def load(meta_path):

        #load .locmeta
        meta = LocMeta.load(meta_path)
        dir = os.path.dirname(meta_path)
        resources = []
        sub_dirs = os.listdir(dir)
        sub_dirs = [d for d in sub_dirs if os.path.exists(os.path.join(dir, d, meta.resource_name+'.locres'))]
        if len(sub_dirs)==0:
            raise RuntimeError('Not found subdirectories for .locres files.')
        if meta.main_lang not in sub_dirs:
            raise RuntimeError('Not found subdirectory for {}.'.format(meta.main_lang))
        if meta.version==1:
            for lang in meta.local_languages:
                if lang not in sub_dirs:
                    raise RuntimeError('Not found subdirectory for {}.'.format(lang))

        #load .locres files            
        for folder in sub_dirs:
            locres_path = os.path.join(dir, folder, meta.resource_name+'.locres')
            if not os.path.exists(locres_path):
                raise RuntimeError('File not found. ({})'.format(locres_path))
            locres = LocRes.load(locres_path)
            resources.append(locres)
        return LocalizationResources(meta, sub_dirs, resources)

    def save_res(out_dir, res, lang, name):
        dir = os.path.join(out_dir, lang)
        mkdir(dir)
        res.save(os.path.join(dir, name+'.locres'))

    def save(self, out_dir):
        resource_name = self.meta.resource_name
        dir = os.path.join(out_dir, resource_name)
        mkdir(dir)
        #save .locmeta
        meta_path = os.path.join(dir, resource_name+'.locmeta')
        self.meta.save(meta_path)
        #save .locres files
        LocalizationResources.save_res(dir, self.main_res, self.meta.main_lang, resource_name)
        for resource, lang in zip(self.resources, self.langs):
            LocalizationResources.save_res(dir, resource, lang, resource_name)
        return meta_path

    def merge_resources(main_res, sub_res, sub_lang):
        for ns in main_res:
            main_res_ns = main_res[ns]
            if ns not in sub_res:
                sub_res_ns = {}
            else:
                sub_res_ns = sub_res[ns]
            for entry in main_res_ns:
                if entry not in sub_res_ns:
                    main_res_ns[entry][sub_lang]=None
                else:
                    main_res_ns[entry][sub_lang] = sub_res_ns[entry]

    def save_as_json(self, out_dir):
        mkdir(out_dir)
        file = self.meta.resource_name + '.json'
        file = os.path.join(out_dir, file)
        j = {'locmeta': self.meta.to_json()}
        j['locmeta']['local_languages'] = self.langs
        j['locmeta']['res_version'] = self.main_res.version

        main_j = self.main_res.to_json_with_lang(self.meta.main_lang)
        resources = [locres.to_json() for locres in self.resources]
        list(map(lambda x, y: LocalizationResources.merge_resources(main_j, x, y), resources, self.langs))
        j['locres']=main_j        
        print('Saving {}...'.format(file))
        save_json(file, j)
        return file

    def generate_hash(resource_json, main_language):
        for ns in resource_json:
            namespace = resource_json[ns]
            for key in namespace:
                entry = namespace[key]
                key_hash = cityhash.string_cityhash(key)
                value_hash = crc.string_crc32(entry[main_language])
                entry['key_hash'] = key_hash
                entry['value_hash'] = value_hash
                if entry[main_language] is None:
                    raise RuntimeError('{}:{}: Value for main language is not found'.format(ns, key))

    def json_to_locres(file):
        print('Loading {}...'.format(file))
        j = load_json(file)
        meta_json = j['locmeta']
        meta_version = meta_json['meta_version']
        resource_name = meta_json['resource_name']
        main_language = meta_json['main_language']
        main_file = os.path.join(main_language, resource_name+'.locres')
        local_langs = meta_json['local_languages']
        meta = LocMeta(meta_version, main_language, main_file, local_langs)
        langs = [main_language] + local_langs
        if 'key_hash' in langs or 'value_hash' in langs:
            raise RuntimeError("Can not use 'key_hash' or 'value_hash' as language.")
        resource_json = j['locres']
        res_version = meta_json['res_version']
        LocalizationResources.generate_hash(resource_json, main_language)
        resources = [LocRes.json_to_locres(res_version, resource_json, lang) for lang in langs]
        return LocalizationResources(meta, langs, resources)
