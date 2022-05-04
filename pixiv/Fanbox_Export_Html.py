html_front = '''
<!DOCTYPE html>
<style>
    html {
        -webkit-text-size-adjust: 100%;
    }

    body {
        font-family: "Helvetica Neue", arial, "Hiragino Kaku Gothic ProN", Meiryo, sans-serif;
        -webkit-font-smoothing: antialiased;
        font-kerning: normal;
    }

    div {
        user-select: text;
        white-space: pre-wrap;
        overflow-wrap: break-word;
        font-size: 48px;
        line-height: 48px;
        color: rgb(32, 32, 32);
        -webkit-tap-highlight-color: transparent;
        cursor: text;
    }
    span {
        display: block;
    }

    img {
        width: 100%;
    }
</style>
<body>
'''


html_end = '''
</body>
'''


def apply_plain(text):
    return '''
    <div>
        <span data-text="true">''' + text + '''</span>
    </div>
    '''


def apply_image(src):
    return '<img src="%s">' % src
