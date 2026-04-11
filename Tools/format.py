import sys
from pygments import highlight
from pygments.lexers import XmlLexer
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from weasyprint import HTML

py_lexer = get_lexer_by_name("python3", stripall=True)
fs_lexer = get_lexer_by_name("fsharp", stripall=True)
txt_lexer = get_lexer_by_name("text", stripall=True)
cpp_lexer = get_lexer_by_name("c++", stripall=True)
xml_lexer = XmlLexer()
style_name="sas"
formatter = HtmlFormatter(linenos=False, full=False, style=style_name)
style_defs = formatter.get_style_defs('.highlight')


def header():
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <style>

          @page {{
            margin: 0.5in;
            size: Letter;
          }}

            body {{ font-family: 'Segoe UI', sans-serif; padding: 40px; background-color: #fff; }}

            /* Code Container */
            .code-box {{
                border: 1px solid #ccc;
                border-radius: 6px;
                overflow: hidden;
                width: 100%;
            }}

            /* Filename Header */
            .file-header {{
                background-color: #e0e0e0;
                color: #333;
                padding: 10px 15px;
                font-size: 14px;
                font-weight: bold;
                border-bottom: 1px solid #ccc;
                font-family: monospace;
            }}

            /* Syntax Highlighting Styles */
            {style_defs}

            .highlight {{ margin: 0; padding: 15px; background-color: #fff; }}
            pre {{ margin: 0; white-space: pre-wrap; font-size: 11px; }}
        </style>
    </head>
    <body>"""


def footer():
    return "</body></html>"


def conv(filename):
    code = ""
    with open(filename, 'r') as file:
        code = file.read()

    if filename.endswith(".fs"):
        code_html = highlight(code, fs_lexer, formatter)
    elif filename.endswith(".py"):
        code_html = highlight(code, py_lexer, formatter)
    elif filename.endswith(".csproj"):
        code_html = highlight(code, xml_lexer, formatter)
    elif filename.endswith(".fsproj"):
        code_html = highlight(code, xml_lexer, formatter)
    elif filename.endswith(".slnx"):
        code_html = highlight(code, xml_lexer, formatter)
    elif filename.endswith(".cpp"):
        code_html = highlight(code, cpp_lexer, formatter)
    elif filename.endswith(".h"):
        code_html = highlight(code, cpp_lexer, formatter)
    elif filename.endswith(".hpp"):
        code_html = highlight(code, cpp_lexer, formatter)

    else:
        code_html = highlight(code, txt_lexer, formatter)

    return f"""
    <div class="code-box">
        <div class="file-header">{filename}</div>
        {code_html}
    </div><BR/>"""


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python script.py file1.fs file2.fs ...")
    else:
        text = header()
        for filename in sys.argv[1:]:
            if filename.startswith("Archive"):
                print("Ignoring:" + filename)
            else:
                print("Processing:" + filename)
                text += conv(filename)

        text += footer()

        #with open("code.html", "w") as file:
        #    file.write(text)

        print("Converting HTML into PDF")
        HTML(string=text).write_pdf('code.pdf')
