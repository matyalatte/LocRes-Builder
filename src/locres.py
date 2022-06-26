import crc
import cityhash
from io_util import *

SUPPORTED_FORMAT = ['json', 'csv']
LINE_FEED = '<LF>'

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

    def gen_hash(self):
        self.key_hash = cityhash.string_cityhash(self.key)
        self.value_hash = crc.string_crc32(self.value)

    def copy_hash(self, entry):
        self.key_hash = entry.key_hash
        self.value_hash = entry.value_hash

    def has_hash(self):
        return self.key_hash is not None
        
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
    def __init__(self, namespace, entries, namespace_hash=None):
        self.namespace_hash = namespace_hash
        self.namespace = namespace
        self.entries = entries
        self.dict = {entry.key: entry for entry in self.entries}

    def __getitem__(self, key):
        return self.dict[key]
    
    def __contains__(self, key):
        return key in self.dict

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

    def to_csv(self):
        return [[self.namespace+"/"+entry.key, entry.value.replace("\n", LINE_FEED)] for entry in self.entries]

    def load_from_json(ns, json):
        entries = []
        for key in json:
            value = json[key]
            if value is not None:
                entries.append(Entry(key, 0, value=value))
        return Namespace(ns, entries)

    def gen_hash(self):
        self.namespace_hash = cityhash.string_cityhash(self.namespace)
        list(map(lambda entry:entry.gen_hash(), self.entries))

    def has_hash(self):
        return self.namespace_hash is not None

    def copy_hash(self, namespace):
        self.namespace_hash = namespace.namespace_hash
        for entry in namespace.entries:
            key = entry.key
            if key in self:
                self[key].copy_hash(entry)
        for entry in self.entries:
            if not entry.has_hash():
                raise RuntimeError("Main resource should have all keys local resources have. ({})".format(entry.key))

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
        self.dict = {ns.namespace: ns for ns in self.namespaces}

    def __getitem__(self, key):
        return self.dict[key]
    
    def __contains__(self, key):
        return key in self.dict

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

    def save_as_text(self, file, fmt='json'):
        if fmt not in SUPPORTED_FORMAT:
            raise RuntimeError('Unsupported format. ({})'.format(fmt))

        print('Saving {}...'.format(file))
        if fmt=='json':
            json = {ns.namespace: ns.to_json() for ns in self.namespaces}
            save_json(file, json)
        elif fmt=='csv':
            csv = sum([ns.to_csv() for ns in self.namespaces], [])
            save_csv(file, [["namespace/key", "value"]]+csv)

    def load_from_text(res_version, file, fmt='json'):
        print('Loading {}...'.format(file))

        if fmt=='json':
            json = load_json(file)
            
        elif fmt=='csv':
            csv = load_csv(file)
            if csv[0][0]=='namespace/key':
                csv = csv[1:]
            json = {}
            for row in csv:
                key = row[0].split("/")
                if len(key)<2:
                    raise RuntimeError('All keys in csv should have a namespace.')
                namespace = key[0]
                key = "/".join(key[1:])
                if namespace not in json:
                    json[namespace]={}
                json[namespace][key]=row[1].replace(LINE_FEED, '\n')

        namespaces = []
        for ns in json:
            namespace = Namespace.load_from_json(ns, json[ns])
            namespaces.append(namespace)
        return LocRes(res_version, namespaces)

    def gen_hash(self):
        list(map(lambda ns:ns.gen_hash(), self.namespaces))

    def copy_hash(self, locres):
        for ns in locres.namespaces:
            key = ns.namespace
            if key in self:
                self[key].copy_hash(ns)
        for ns in self.namespaces:
            if not ns.has_hash():
                raise RuntimeError("Main resource should have all namespaces local resources have. ({})".format(ns.namespace))

class LocMeta:
    MAGIC_GUID = b'\x4F\xEE\x4C\xA1\x68\x48\x55\x83\x6C\x4C\x46\xBD\x70\xDA\x50\x7C'

    def __init__(self, version, main_language, main_file, local_languages):
        self.version = version
        self.main_language = main_language
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
            main_language = read_str(f)
            main_file = read_str(f)
            if version==1:
                local_languages = read_str_array(f)
                local_languages.remove(main_language)
            else:
                local_languages = None
        print('Main language: {}'.format(main_language))
        print('Main resource: {}'.format(main_file))
        return LocMeta(version, main_language, main_file, local_languages)

    def save(self, file):
        print('Saving {}...'.format(file))
        with open(file, 'wb') as f:
            f.write(LocMeta.MAGIC_GUID)
            write_uint8(f, self.version)
            write_str(f, self.main_language)
            write_str(f, self.main_file.replace('\\', '/'))
            if self.version==1:
                languages = self.local_languages+[self.main_language]
                write_str_array(f, sorted(list(set(languages))), with_length=True)

    def save_as_text(self, file, res_version, fmt='json'):
        print('Saving {}...'.format(file))
        if fmt=='json':
            self.save_as_json(file, res_version)
        elif fmt=='csv':
            self.save_as_csv(file, res_version)

    def save_as_json(self, file, res_version):
        json = {
            'locmeta_version': self.version,
            'locres_version': res_version,
            'resource_name': self.resource_name,
            'main_language': self.main_language,
            'local_languages': self.local_languages
        }
        save_json(file, json)

    def save_as_csv(self, file, res_version):
        local_langs = '{}'.format(self.local_languages)[1:-1].replace("'", "")
        csv = [
            ["key", "value"],
            ['locmeta_version', self.version],
            ['locres_version', res_version],
            ['resource_name', self.resource_name],
            ['main_language', self.main_language],
            ['local_languages', local_langs]
        ]
        save_csv(file, csv)

    def load_from_text(file, fmt='json'):
        if fmt not in SUPPORTED_FORMAT:
            raise RuntimeError('Unsupported format. ({})'.format(fmt))
        
        print('Loading {}...'.format(file))
        if fmt=='json':
            json = load_json(file)
        elif fmt=='csv':
            csv = load_csv(file)
            if csv[0][0]=='key':
                csv = csv[1:]
            json = {row[0]:row[1] for row in csv}
            json['locmeta_version']=int(json['locmeta_version'])
            json['locres_version']=int(json['locres_version'])
            json['local_languages']=json['local_languages'].replace(" ", "").split(',')

        version = json['locmeta_version']
        resource_name = json['resource_name']
        main_language = json['main_language']
        local_languages = json['local_languages']
        main_file = os.path.join(main_language, resource_name+'.locres')
        locmeta = LocMeta(version, main_language, main_file, local_languages)
        return locmeta, json['locres_version']
        
class LocalizationResources:
    def __init__(self, meta, langs, resources):
        self.meta = meta
        self.langs = langs
        self.resources = resources
        
        main_id = self.langs.index(self.meta.main_language)
        main_language = self.langs.pop(main_id)
        self.main_res = self.resources.pop(main_id)

        #print entry count for each language
        print(main_language)
        self.main_res.print()
        for lang, res in zip(langs, resources):
            print(lang)
            if res is not None:
                res.print()
            else:
                print('  File not found.')

    def load(meta_path):

        #load .locmeta
        meta = LocMeta.load(meta_path)
        dir = os.path.dirname(meta_path)
        resources = []
        sub_dirs = os.listdir(dir)
        sub_dirs = [d for d in sub_dirs if os.path.exists(os.path.join(dir, d, meta.resource_name+'.locres'))]
        if len(sub_dirs)==0:
            raise RuntimeError('Not found subdirectories for .locres files.')
        if meta.main_language not in sub_dirs:
            raise RuntimeError('Not found subdirectory for {}.'.format(meta.main_language))
        
        if meta.local_languages is None:
            meta.local_languages=sub_dirs

        #load .locres files            
        for folder in sub_dirs:
            locres_path = os.path.join(dir, folder, meta.resource_name+'.locres')
            if not os.path.exists(locres_path):
                raise RuntimeError('File not found. ({})'.format(locres_path))
            locres = LocRes.load(locres_path)
            resources.append(locres)

        if meta.version==1:
            for lang in meta.local_languages:
                if lang not in sub_dirs:
                    sub_dirs.append(lang)
                    resources.append(None)
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
        LocalizationResources.save_res(dir, self.main_res, self.meta.main_language, resource_name)
        for resource, lang in zip(self.resources, self.langs):
            if resource is None:
                continue
            LocalizationResources.save_res(dir, resource, lang, resource_name)

        return meta_path

    def save_as_text(self, out_dir, fmt='json'):
        if fmt not in SUPPORTED_FORMAT:
            raise RuntimeError('Unsupported format. ({})'.format(fmt))

        dir = os.path.join(out_dir, self.meta.resource_name)
        mkdir(dir)

        #save locmeta
        meta_file = os.path.join(dir, 'locmeta.{}'.format(fmt))
        self.meta.save_as_text(meta_file, self.main_res.version, fmt=fmt)

        #save locres
        for locres, lang in zip([self.main_res]+self.resources, [self.meta.main_language]+self.langs):
            if locres is None:
                continue
            file = '{}.{}'.format(lang, fmt)
            file = os.path.join(dir, file)
            locres.save_as_text(file, fmt=fmt)

        return meta_file

    def load_from_text(file, fmt='json'):
        dir = os.path.dirname(file)
        file = os.path.join(dir,'locmeta.{}'.format(fmt))
        if not os.path.exists(file):
            raise RuntimeError('File not found ({})'.format(file))

        #load locmeta data
        meta, res_version = LocMeta.load_from_text(file, fmt=fmt)
        langs = [meta.main_language] + meta.local_languages

        #load locres data
        res_files = ['{}.{}'.format(lang, fmt) for lang in langs]
        res_files = [os.path.join(dir, file) for file in res_files]
        if not os.path.exists(res_files[0]):
            raise RuntimeError('Main resource file not found. ({})'.format(res_files[0]))
        resources = []
        for file in res_files:
            if os.path.exists(file):
                res = LocRes.load_from_text(res_version, file, fmt=fmt)
            else:
                res = None
            resources.append(res)

        #generate hash
        resources[0].gen_hash()
        for res in resources[1:]:
            if res is not None:
                res.copy_hash(resources[0])

        return LocalizationResources(meta, langs, resources)
