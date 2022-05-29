import os, argparse, shutil
from locres import LocalizationResources
from io_util import compare, get_ext

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('file', help='.locmeta')
    parser.add_argument('--out_dir', default = '', help='Output path')
    parser.add_argument('--test', action='store_true', help='Check if the script can reconstruct locres files or not.')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = get_args()
    file = args.file
    out_dir = args.out_dir
    ext = get_ext(file)
    if args.test:
        if ext!='locmeta':
            raise RuntimeError('Specify a .locmeta file.')
        out_dir = '__temp__'
        locres = LocalizationResources.load(file)
        json_path = locres.save_as_json(out_dir)
        new_locres = LocalizationResources.json_to_locres(json_path)
        meta_path = new_locres.save(out_dir)
        compare(os.path.dirname(meta_path), os.path.dirname(file))
        shutil.rmtree(out_dir)
    else:
        if ext=='locmeta':
            locres = LocalizationResources.load(file)
            json_path = locres.save_as_json(out_dir)
        elif ext=='json':
            locres = LocalizationResources.json_to_locres(file)
            meta_path = locres.save(out_dir)
        else:
            raise RuntimeError('Unsupported extension detected. Use .locmeta or .json. ({})'.format(ext))
    print('Done!')