import re
import os
import sys
import glob
import requests
from bs4 import BeautifulSoup

debug = False


def slugify(value):
    """Slugify filenames identically to gallery-dl,
    but also remove beginning of urls."""

    value = re.sub(r"^https?:/+", "", str(value).lower())
    value = re.sub(r"[^\w\s-]", "", value)
    return re.sub(r"[-\s]+", "-", value).strip("-_")


def expanded_directory(path, must_exist=True):
    """Return absolute directory of given path and filename if applicable."""

    path = os.path.expandvars(path)
    path = os.path.expanduser(path)
    path = os.path.abspath(path)
    filename = None
    if must_exist:
        assert os.path.exists(path)
        if os.path.isfile(path):
            path, filename = os.path.split(path)
    else:
        if '.' in os.path.split(path)[1]:
            path, filename = os.path.split(path)
    return path, filename


def relative_path(absolute_file, relative_to, must_exist=True):
    """Calculate relative path of a file compared to another."""

    absolute_file, filename = expanded_directory(absolute_file,
                                                 must_exist=must_exist)
    relative_to, _ = expanded_directory(relative_to, must_exist=must_exist)
    assert filename

    stem = os.path.commonpath([absolute_file, relative_to])
    absolute_file = absolute_file.replace(stem, '').lstrip(os.sep)
    relative_to = relative_to.replace(stem, '').lstrip(os.sep)

    abs_p = absolute_file.split(os.sep) if len(absolute_file) > 0 else []
    ref_p = relative_to.split(os.sep) if len(relative_to) > 0 else []
    rel_p = ['..']*len(ref_p)

    relative_path = os.path.join(*rel_p, *abs_p, filename)
    full_path = os.path.join(stem, relative_to, relative_path)
    if must_exist:
        assert os.path.isfile(full_path)
    return relative_path


def main():
    """Correct downloaded metadata by linking to local files
    and downloading avatars and emojis."""

    # Get both data file and metadata file
    # Depend on deviantart.directory and metadata.directory settings.
    targetfile = sys.argv[1]
    folder = sys.argv[2]
    username = sys.argv[4]
    metafilename = os.path.splitext(sys.argv[3])[0] + '.html'
    metafile = os.path.join(folder, '..', 'html', metafilename)  # VARIABLE
    assert os.path.isfile(targetfile)
    assert os.path.isfile(metafile)

    # Modify html file(s)
    editfiles = [metafile]
    if os.path.splitext(targetfile)[1] in {'.html', '.htm'}:
        editfiles.append(targetfile)

    for editfile in editfiles:
        if debug:
            print('File:', editfile)
        with open(editfile) as fp:
            soup = BeautifulSoup(fp, 'html.parser')

        # replace external images
        # put them in deviantart/assets directory
        images = soup.find_all('img')
        assetsdir = folder.split(os.sep)
        assetsdir = os.sep.join([*assetsdir[:assetsdir.index('deviantart')+1],
                                 'assets'])  # VARIABLE
        if not os.path.exists(assetsdir):
            os.makedirs(assetsdir)

        for image in images:
            url = image['src']
            if url.startswith("http"):
                if debug:
                    print('Want to replace image', url)
                filename, ext = os.path.splitext(url)
                ext = re.match(r"(\.\w+)", ext).group()
                fullpath = os.path.join(assetsdir, slugify(filename) + ext)

                if not os.path.exists(fullpath):
                    with open(fullpath, 'wb') as f:
                        resp = requests.get(url)
                        f.write(resp.content)

                if os.path.exists(fullpath):
                    path = relative_path(fullpath, editfile, must_exist=False)
                    image['src'] = path
                else:
                    print('Unable to replace', url)

        # replace links to my deviations by local relative links
        links = soup.find_all('a')
        criteria = (r'^https?://' +
                    r'(www\.deviantart\.com/{u}|' +
                    r'{u}\.deviantart\.com)/.+').format(u=username)
        for link in links[1:]:  # keep first one in template # VARIABLE
            url = link['href']
            if re.match(criteria, url):
                if debug:
                    print('Want to replace link', url)
                deviation = os.path.split(url)[-1]
                deviation = '-'.join(deviation.split('-')[:-1])
                deviation = '*' + slugify(deviation) + '.html'
                deviation = os.path.join(folder, '../html', deviation)  # VARIABLE
                candidates = glob.glob(deviation, recursive=True)

                if len(candidates) == 1:
                    path = relative_path(candidates[0], editfile)
                    link['href'] = path
                elif len(candidates) > 1:
                    print('Too many candidates for', url)
                else:
                    print('No candidates for', url, 'with search', deviation)

        # Save modifications
        with open(editfile, 'w') as fp:
            fp.write(str(soup))


if __name__ == "__main__":
    main()
