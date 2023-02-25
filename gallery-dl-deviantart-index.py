import os
import sys
import datetime
from bs4 import BeautifulSoup

template = ('<!DOCTYPE html>\n<html>\n<head>\n' +
            '<link href="https://cdn.simplecss.org/simple.min.css" ' +
            'rel="stylesheet"/>\n' +
            '<title>Gallery {u}</title>\n' +
            '</head>\n<style>\n' +
            '.gallery {{column-count: 3;}}\n' +
            '.gallery a {{text-decoration: none; color: inherit;}}\n' +
            '.gallery a:hover {{filter: grayscale(0%);}}\n' +
            '.gallery img, .gallery div {{margin: 5px; width: 100%;' +
            'border: 1px solid; border-radius: 5px;}}\n' +
            '.gallery div {{padding: 1em 0;' +
            'text-align: center; vertical-align: middle;}}\n' +
            '</style>\n<body>\n<header>\n' +
            '<h1>Gallery {u}</h1>\n' +
            '{s}</header>\n<main>\n' +
            '<div class="gallery">\n{i}</div>\n'
            '</main>\n</body>\n</html>\n')


def relative_image(file, directory):
    """Return relative path to image."""

    dir = './images'  # VARIABLE
    path = os.path.normpath(os.path.join(*dir.split(os.sep), file))
    fullpath = os.path.join(directory, path)
    assert os.path.exists(fullpath)
    return path


def relative_metadata(file, directory):
    """Return relative path to metadata html page."""

    dir = './html'  # VARIABLE
    filename = os.path.splitext(file)[0] + '.html'
    path = os.path.normpath(os.path.join(*dir.split(os.sep), filename))
    fullpath = os.path.join(directory, path)
    assert os.path.exists(fullpath)
    return path


def statistics(files):
    """Show information about the age and number of files."""

    datefmt = '%d %b %Y'
    n = len(files)
    string = '{} deviations<br/>\n'.format(n)
    if n > 1:
        dates = [datetime.datetime.strptime(f.split('_')[1], '%Y%m%d')
                 for f in (files[0], files[-1])]
        string += '{f} → {l}\n'.format(f=dates[0].strftime(datefmt),
                                       l=dates[1].strftime(datefmt))
    return string


def textual_gallery(metadata, directory):
    """Generate a div showing textual content from its metadata."""

    file = os.path.join(directory, metadata)
    with open(file) as fp:
        soup = BeautifulSoup(fp, 'html.parser')
    return '<div>{}</div>'.format(soup.title.string)


def gallery(directory, user=None):
    """List all deviations and generate an index in directory
    to display them as a chronological gallery.
    If passing a username, restrict to filenames starting with it."""

    imgdir = os.path.join(directory, relative_image('', directory))
    files = [f for f in os.listdir(imgdir)
             if os.path.isfile(os.path.join(imgdir, f))
             and f != 'index.html']
    files = sorted(files, key=lambda f: int(f.split('_')[1]))
    txt = ''

    statstxt = statistics(files)

    for file in files:
        src = relative_image(file, directory)
        href = relative_metadata(file, directory)
        if os.path.splitext(file)[1] in {'.html', '.htm'}:
            img = textual_gallery(href, directory)
        else:
            img = '<img src="{}">'.format(src)
        txt += '<a href="{}">{}</a>\n'.format(href, img)

    return txt, statstxt


def main(directory, user=None):
    """Fill the html template with the generated gallery.
    Argument: directory where to create the index.
    The path to the images and metadata are set in the
    relative_image and relative_metadata functions and should match
    the deviantart.directory and metadata.directory settings."""

    images, stats = gallery(directory, user)
    username = 'of '+user.capitalize() if user else ''
    html = template.format(s=stats, i=images, u=username)

    # Save modifications
    file = os.path.join(directory, 'index.html')
    with open(file, 'w') as fp:
        fp.write(html)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(*sys.argv[1:])
