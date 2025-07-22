import os
import tkinter as tk
from tkinter import (
    Tk, Frame, Label, Button, Entry, filedialog, messagebox, scrolledtext, Checkbutton
)
from tkinter.ttk import Button, Label, Frame
import requests
import webbrowser
try:
    from tkhtmlview import HTMLLabel
    _HAS_TKHTMLVIEW = True
except ImportError:
    _HAS_TKHTMLVIEW = False

# 配置OpenRouter API Key（可在环境变量OPENROUTER_API_KEY设置，或直接填写）
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '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')

HTML_DIR = os.path.join(os.path.dirname(__file__), 'strategy_html')
os.makedirs(HTML_DIR, exist_ok=True)


# 调用OpenRouter生成HTML的函数
def generate_html_from_py(py_path):
    import os
    OPENROUTER_API_URL = 'https://openrouter.ai/api/v1/chat/completions'
    MODEL = 'nvidia/llama-3.1-nemotron-ultra-253b-v1:free'
    cci_html_path = os.path.join(os.path.dirname(__file__), 'AlligatorStrat.html')
    with open(cci_html_path, 'r', encoding='utf-8') as f:
        cci_html_template = f.read()
    with open(py_path, 'r', encoding='utf-8') as f:
        py_code = f.read()
    prompt = (
        "你是一个Freqtrade策略文档助手。请将以下Python策略代码，生成详细的HTML文档，格式严格参考下面给出的CCIStrategy.html模板内容。"
        "【重要要求】\n"
        "1. 必须输出完整的HTML文件内容（包含<!DOCTYPE html>、<html>、<head>、<body>等标签）；\n"
        "2. 【必须】禁止输出任何Markdown代码块标记（如```html、```等），也禁止输出任何与HTML无关的注释或说明，只能输出纯HTML文件内容！\n"
        "3. 内容要结构化、详细、中文输出，且生成结果可以直接保存为.html文件并在浏览器中打开；\n"
        "4. 【必须】在HTML页面最顶端添加一个返回上一级目录的链接，链接地址为 ../strategy_index.html，链接文本为‘返回策略索引’，样式与页面协调。\n"
        "5. 【必须】在HTML表格下方单独添加一节，对所有交易变量（如：策略用到的指标、参数、变量等）进行详细解释，可以举例说明每个变量的实际含义和作用，内容结构清晰，便于理解。\n"
        "【CCIStrategy.html模板如下】\n" + cci_html_template +
        "\n【待处理的策略代码如下】\n" + py_code +
        "6. 请确保总结的信息能够明确说明交易策略的逻辑，包括但不限于：交易条件、交易信号、交易参数、交易逻辑等。\n"
        "7. 【必须】禁止输出任何```html、```等代码块标记或与HTML无关的注释，只能输出HTML文件内容！\n"
    )
    headers = {
        'Authorization': f'Bearer {OPENROUTER_API_KEY}',
        'Content-Type': 'application/json',
    }
    data = {
        'model': MODEL,
        'messages': [
            {"role": "user", "content": prompt}
        ],
        'inference_mode': True
    }
    response = requests.post(OPENROUTER_API_URL, headers=headers, json=data, timeout=60)
    if response.status_code != 200:
        raise RuntimeError(f'OpenRouter API请求失败: {response.status_code} {response.text}')
    resp_json = response.json()
    html = resp_json['choices'][0]['message']['content']
    return html

def save_html(py_path, html_content):
    base = os.path.splitext(os.path.basename(py_path))[0]
    html_path = os.path.join(HTML_DIR, base + '.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    return html_path

class OpenAIGui(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Freqtrade策略HTML生成器')
        self.geometry('900x700')
        self.create_widgets()

    def create_widgets(self):
        frame = Frame(self)
        frame.pack(padx=10, pady=10, fill='x')

        self.file_label = Label(frame, text='选择Python文件:')
        self.file_label.grid(row=0, column=0, sticky='w')
        self.file_path_var = tk.StringVar()
        self.file_entry = tk.Entry(frame, textvariable=self.file_path_var, width=60)
        self.file_entry.grid(row=0, column=1, padx=5)
        Button(frame, text='浏览', command=self.browse_file).grid(row=0, column=2)
        Button(frame, text='生成并预览HTML', command=self.gen_and_preview_html).grid(row=0, column=3, padx=5)

        self.dir_label = Label(frame, text='选择目录:')
        self.dir_label.grid(row=1, column=0, sticky='w')
        self.dir_path_var = tk.StringVar()
        self.dir_entry = tk.Entry(frame, textvariable=self.dir_path_var, width=60)
        self.dir_entry.grid(row=1, column=1, padx=5)
        Button(frame, text='浏览', command=self.browse_dir).grid(row=1, column=2)
        Button(frame, text='批量生成HTML', command=self.batch_gen_html).grid(row=1, column=3, padx=5)

        self.overwrite_html_var = tk.BooleanVar(value=False)
        Checkbutton(frame, text='覆盖已存在HTML', variable=self.overwrite_html_var).grid(row=2, column=1, sticky='w')

        self.status_var = tk.StringVar(value='')
        tk.Label(self, textvariable=self.status_var, fg='blue').pack(pady=5)

        # HTML渲染预览
        if _HAS_TKHTMLVIEW:
            self.html_preview = HTMLLabel(self, html='', width=110, height=32, background='white')
            self.html_preview.pack(fill='both', expand=True, padx=10, pady=5)
        else:
            self.html_preview = scrolledtext.ScrolledText(self, wrap='word', width=110, height=32)
            self.html_preview.pack(fill='both', expand=True, padx=10, pady=5)
        Button(self, text='在浏览器中打开HTML', command=self.open_in_browser).pack(pady=5)

    def browse_file(self):
        path = filedialog.askopenfilename(filetypes=[('Python Files', '*.py')])
        if path:
            self.file_path_var.set(path)

    def browse_dir(self):
        path = filedialog.askdirectory()
        if path:
            self.dir_path_var.set(path)

    def gen_and_preview_html(self):
        py_path = self.file_path_var.get()
        if not py_path or not os.path.isfile(py_path):
            messagebox.showerror('错误', '请选择有效的Python文件')
            return
        try:
            self.status_var.set('正在生成HTML...')
            self.update()
            html = generate_html_from_py(py_path)
            html_path = save_html(py_path, html)
            if _HAS_TKHTMLVIEW:
                self.html_preview.set_html(html)
            else:
                self.html_preview.delete('1.0', tk.END)
                self.html_preview.insert(tk.END, html)
            self.status_var.set(f'HTML已生成: {html_path}')
            self.current_html_path = html_path
        except Exception as e:
            self.status_var.set('生成失败')
            messagebox.showerror('错误', str(e))

    def batch_gen_html(self):
        dir_path = self.dir_path_var.get()
        if not dir_path or not os.path.isdir(dir_path):
            messagebox.showerror('错误', '请选择有效的目录')
            return
        py_files = [os.path.join(dir_path, f) for f in os.listdir(dir_path) if f.endswith('.py')]
        if not py_files:
            messagebox.showinfo('提示', '目录下没有Python文件')
            return
        failed = []
        for py_path in py_files:
            base = os.path.splitext(os.path.basename(py_path))[0]
            html_path = os.path.join(HTML_DIR, base + '.html')
            if not self.overwrite_html_var.get() and os.path.exists(html_path):
                print(f"已存在HTML，跳过: {html_path}")
                continue
            print(f"正在处理: {py_path}")  # 控制台输出当前文件路径
            try:
                self.status_var.set(f'正在生成: {os.path.basename(py_path)}')
                self.update()
                html = generate_html_from_py(py_path)
                html_path = save_html(py_path, html)
                print(f"已保存为HTML: {html_path}")  # 打印保存成功
            except Exception as e:
                print(f"保存失败: {py_path}, 错误: {e}")  # 打印保存失败
                failed.append(os.path.basename(py_path))
        # 生成索引HTML
        try:
            index_html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'strategy_index.html')
            rows = []
            serial = 1
            for py_path in py_files:
                base = os.path.splitext(os.path.basename(py_path))[0]
                html_path = os.path.join(HTML_DIR, base + '.html')
                if os.path.exists(html_path):
                    strategy_name = base
                    py_rel = os.path.relpath(py_path, os.path.dirname(index_html_path)).replace('\\', '/')
                    html_rel = os.path.relpath(html_path, os.path.dirname(index_html_path)).replace('\\', '/')
                    rows.append(f'<tr><td>{serial}</td><td>{strategy_name}</td><td><a href="{py_rel}">{os.path.basename(py_path)}</a></td><td><a href="{html_rel}">{os.path.basename(html_path)}</a></td></tr>')
                    serial += 1
            table = (
                '<html><head><meta charset="utf-8"><title>策略索引</title></head><body>'
                '<h2>策略索引</h2>'
                '<table border="1" cellpadding="6" style="border-collapse:collapse;">'
                '<tr style="background:#f0f0f0;"><th>序列号</th><th>策略名称</th><th>Python文件</th><th>HTML文档</th></tr>'
                + '\n'.join(rows) +
                '</table></body></html>'
            )
            with open(index_html_path, 'w', encoding='utf-8') as f:
                f.write(table)
            print(f"已生成索引: {index_html_path}")
        except Exception as e:
            print(f"生成索引文件失败: {e}")

        if failed:
            self.status_var.set(f'部分文件生成失败: {failed}')
        else:
            self.status_var.set('全部HTML已生成')
        messagebox.showinfo('完成', '批量处理完成')

    def open_in_browser(self):
        if hasattr(self, 'current_html_path') and os.path.isfile(self.current_html_path):
            webbrowser.open('file://' + os.path.abspath(self.current_html_path))
        else:
            messagebox.showinfo('提示', '请先生成HTML')

if __name__ == '__main__':
    app = OpenAIGui()
    app.mainloop()
