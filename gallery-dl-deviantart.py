import os
import re
import datetime
import mimetypes


def slugify(value):
    """Slugify filenames identically to gallery-dl"""
    value = re.sub(r"[^\w\s-]", "", str(value).lower())
    return re.sub(r"[-\s]+", "-", value).strip("-_")


def filename(data):
    """Get relative url of file whose metadata this is.
    Depend on deviantart.directory and metadata.directory settings."""
    string = os.path.join('..', 'images', '{u}_{d}_{t}.{e}')  # VARIABLE
    return string.format(u=data['username'],
                         d=data['date'].strftime('%Y%m%d'),
                         t=slugify(data['title']),
                         e=data['extension'])


def head(data):
    """Generate HTML head, including minimal external CSS."""
    string = ('<head>\n' +
              '<link rel="stylesheet" ' +
              'href="https://cdn.simplecss.org/simple.min.css">\n' +
              '<title>{}</title>\n' +
              '</head>\n')
    return string.format(data['title'])


def header(data):
    """Generate page header with infos about the picture."""
    if 'tags' in data and len(data['tags']) > 0:
        tags = 'tags: ' + ' - '.join(data['tags']) + '<br>\n'
    else:
        tags = ''

    if 'license' in data and data['license'] != 'No License':
        artlicense = data['license'] + '<br>\n'
    else:
        artlicense = ''

    if 'stats' in data:
        stats = []
        for key in data['stats'].keys():
            stats.append('{} {}'.format(data['stats'][key], key))
        stats = ', '.join(stats) + '<br>\n'
    else:
        stats = ''

    if 'author' in data and 'usericon' in data['author']:
        avatar = ('<img src="{}" style="vertical-align: middle; ' +
                  'margin-right: 10px;">\n').format(data['author']['usericon'])
    else:
        avatar = ''

    date = data['date'].strftime('%a %d %m %Y, %X')
    url = '<a href="{}">{}</a><br>\n'.format(data['url'], date)

    category = data['subcategory']
    if 'category_path' in data:
        category += ': {}<br>\n'.format(data['category_path'])

    string = ('<header>\n' +
              '<h1>{T}</h1>\n{a}' +
              '<div style="display:inline-block; vertical-align: middle; ' +
              'text-align: left;">\n' +
              '{u}{c}{s}{t}{l}</div>\n</header>\n')
    return string.format(T=data['title'], a=avatar, u=url, c=category,
                         s=stats, t=tags, l=artlicense)


def figure(data):
    """Generate section to show the picture, or a thumbnail if available."""
    if 'extension' in data:
        kind = mimetypes.guess_type('filename.' + data['extension'])
        if 'image' in kind[0]:
            img = filename(data)
        elif 'thumbs' in data and len(data['thumbs']) > 0:
            img = data['thumbs'][0]['src']
        else:
            return ''

        string = ('<figure style="text-align: center;">\n' +
                  '<a href="{}">' +
                  '<img style="max-width: 100%;" src="{}">' +
                  '</a>\n</figure>\n')
        return string.format(filename(data), img)
    return ''


def description(data):
    """Generate section with the art description."""
    if 'description' in data and len(data['description']) > 0:
        return '<h2>Description</h2>\n{}\n'.format(data['description'])
    return ''


def text(data):
    """For texts, generate section with an exerpt and link to full text."""
    if 'excerpt' in data:
        string = ('<h2>Excerpt</h2>\n' +
                  '<p>{}… → <a href="{}">full version</a>' +
                  '</p>\n')
        return string.format(data['excerpt'], filename(data))
    return ''


def comments(data):
    """Generate comment section."""
    if 'comments' in data and len(data['comments']) > 0:
        text = '<h2>Comments</h2>\n'
        indent = {}  # thread indendation
        string = ('<article style="margin-left: {i}px;">\n<footer>\n' +
                  '<img src="{a}" style="float: left; margin-right: 10px;">' +
                  '\n<b>{u}</b><br>\n{d}{r}\n</footer>\n' +
                  '<p style="clear: both;">\n{b}\n</p>\n</article>')
        datefmt = '%a %d %b %Y, %X'

        for comment in data['comments']:
            id = comment['commentid']
            body = comment['body']
            user = comment['user']['username']
            avatar = comment['user']['usericon']

            date = datetime.datetime.strptime(comment['posted'],
                                              '%Y-%m-%dT%H:%M:%S%z')
            date = '<span id={}>{}</span>'.format(id, date.strftime(datefmt))

            replies = comment['replies']
            if replies == 0:
                replies = ''
            elif replies == 1:
                replies = ' - 1 reply'
            else:
                replies = ' - {} replies'.format(replies)

            parent = comment['parentid']
            if parent:
                date += ' - <a href="#{}">parent</a>'.format(parent)
                indent[id] = indent[parent]+1
            else:
                indent[id] = 0

            text += string.format(i=10*indent[id], a=avatar, u=user,
                                  d=date, r=replies, b=body)
        return text
    return ''


def main(data):
    """Insert the metadata given by gallery-dl into an adapted HTLM template,
    and return as string."""

    string = ('<!DOCTYPE html><html>\n{}\n' +
              '<body>\n{}\n' +
              '<main>\n{}\n</main>\n' +
              '{}\n</body>\n</html>')

    return string.format(head(data), header(data),
                         figure(data) + description(data) + text(data),
                         comments(data))
