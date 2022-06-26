import os, argparse, shutil
from locres import LocalizationResources
from io_util import compare, get_ext

VERSION = '0.1.2'
SUPPORTED_FORMAT = ['json', 'csv']

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('file', help='.locmeta')
    parser.add_argument('-o', '--out_dir', default = '', help='Output path')
    parser.add_argument('-f', '--format', default = 'json', help='json or csv')
    parser.add_argument('--test', action='store_true', help='Check if the script can reconstruct locres files or not.')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    print('LocRes Builder ver{} by matyalatte'.format(VERSION))
    args = get_args()
    file = args.file
    fmt = args.format
    if fmt not in SUPPORTED_FORMAT:
        raise RuntimeError('Unsupported format. ({})'.format(fmt))

    ext = get_ext(file)
    if args.test:
        if ext!='locmeta':
            raise RuntimeError('Specify a .locmeta file.')
        for fmt in SUPPORTED_FORMAT:
            out_dir = '__temp__'
            if os.path.exists(out_dir):
                shutil.rmtree(out_dir)
            locres = LocalizationResources.load(file)
            text_path = locres.save_as_text(out_dir, fmt=fmt)
            new_locres = LocalizationResources.load_from_text(text_path, fmt=fmt)
            meta_path = new_locres.save(out_dir)
            compare(os.path.dirname(meta_path), os.path.dirname(file), ext=['locres', 'locmeta'], rec=2)
            shutil.rmtree(out_dir)
    else:
        out_dir = args.out_dir
        if ext=='locmeta':
            locres = LocalizationResources.load(file)
            json_path = locres.save_as_text(out_dir, fmt=fmt)
        elif ext in SUPPORTED_FORMAT:
            locres = LocalizationResources.load_from_text(file, fmt=ext)
            meta_path = locres.save(out_dir)
        else:
            raise RuntimeError('Unsupported extension detected. Use locmeta, json, or csv. ({})'.format(ext))
    nones = [lang for res, lang in zip(locres.resources, locres.langs) if res is None]
    if len(nones)==0:
        print('Done!')
    elif len(nones)==1:
        print('Warning: A resource file for {} not found.'.format(nones[0]))
    else:
        langs = '{}'.format(nones).replace("'", '')[1:-1]
        print('Warning: Some resource files for local languages not found. ({})'.format(langs))
