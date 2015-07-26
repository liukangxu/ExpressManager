from tkinter import *
from tkinter.scrolledtext import *
from tkinter.ttk import *
import json
import urllib.request


class ExpressQuery(Frame):
    def __init__(self, master):
        Frame.__init__(self, master)
        self.root = master
        self.root.bind_all('<F5>', self.update_all_posts)
        self.all_posts = {}  # 运单列表
        self.root.title('快递助手 v1.0')
        self.root.iconbitmap('logo.ico')
        self.root.resizable(width=False, height=False)

        self.auto_company_url = 'http://www.kuaidi100.com/autonumber/autoComNum?text='
        self.query_url = 'http://www.kuaidi100.com/query?'

        with open('company_codes.json', 'r', encoding='utf-8') as f:
            self.company_codes = json.loads(f.read())
            self.company_names = dict((v, k) for k, v in self.company_codes.items())
        with open('state.json', 'r', encoding='utf-8') as f:
            self.state = json.loads(f.read())

        parent_frame = Frame(self.root)
        parent_frame.grid(padx=10, pady=10, stick=E + W + N + S)

        add_post_group = Frame(parent_frame)
        post_id_label = Label(add_post_group, text='运单号:')
        self.post_id_var = StringVar()  # 运单号
        self.post_id_field = Entry(add_post_group, width=20, textvariable=self.post_id_var)
        self.post_id_field.bind('<Return>', self.add_post)
        post_note_label = Label(add_post_group, text='备注:')
        self.post_note_var = StringVar()  # 运单注释
        post_note_field = Entry(add_post_group, width=20, textvariable=self.post_note_var)
        post_note_field.bind('<Return>', self.add_post)
        post_company_label = Label(add_post_group, text='公司：')
        self.post_company_name_var = StringVar()
        self.post_company_field = Combobox(add_post_group, textvariable=self.post_company_name_var,
                                           values=list(self.company_names.keys()), width=12)
        post_add_button = Button(add_post_group, text='添加', width=10, command=self.add_post)

        post_id_label.grid(row=0, column=0)
        self.post_id_field.grid(row=0, column=1)
        post_note_label.grid(row=0, column=2)
        post_note_field.grid(row=0, column=3)
        post_company_label.grid(row=0, column=4)
        self.post_company_field.grid(row=0, column=5)
        post_add_button.grid(row=0, column=6, padx=5)
        self.post_id_field.focus_set()
        show_posts_group = Frame(parent_frame)
        self.posts = Treeview(show_posts_group, height=10, selectmode='browse',
                              columns=('note', 'company_name', 'state', 'last_update'))  # 运单列表框
        self.x_scrollbar = Scrollbar(show_posts_group, orient=HORIZONTAL, command=self.posts.xview)
        self.y_scrollbar = Scrollbar(show_posts_group, orient=VERTICAL, command=self.posts.yview)
        self.posts.config(xscroll=self.x_scrollbar.set, yscroll=self.y_scrollbar.set)
        self.posts.column('#0', width=130)
        self.posts.heading('#0', text='运单号')
        self.posts.column('note', width=130)
        self.posts.heading('note', text='备注')
        self.posts.column('company_name', width=80)
        self.posts.heading('company_name', text='公司名称')
        self.posts.column('state', width=180)
        self.posts.heading('state', text='运单状态')
        self.posts.column('last_update', width=150)
        self.posts.heading('last_update', text='最后更新')
        self.posts.bind('<<TreeviewSelect>>', self.show_post_detail)
        self.posts.bind('<Delete>', self.remove_post)
        self.post_detail = ScrolledText(show_posts_group, bg='white', width=92, height=16, state=DISABLED)  # 运单记录文本框
        self.posts.grid(row=0, column=0, sticky=W + N + S)
        self.x_scrollbar.grid(row=1, column=0, sticky=E + W)
        self.y_scrollbar.grid(row=0, column=1, sticky=N + S)
        self.post_detail.grid(row=2, column=0, sticky=W + N + S, padx=(0, 10))
        status_label = Label(parent_frame, text='F5 更新全部运单动态')

        add_post_group.grid(row=0, column=0)
        show_posts_group.grid(row=1, column=0)
        status_label.grid(row=2, column=0)

        self.get_history()

    # 获取运单记录
    def get_history(self):
        try:
            with open('history.json', 'r', encoding='utf-8') as f:
                self.all_posts = json.loads(f.read())
            for post_id in self.all_posts:
                self.posts.insert('', 0, post_id, text=post_id,
                                  values=(self.all_posts[post_id]['note'],
                                          self.all_posts[post_id]['company_name'],
                                          self.state[self.all_posts[post_id]['state']],
                                          self.all_posts[post_id]['last_update']))
        except ValueError:
            print('error')

    # 保存运单记录
    def save_history(self):
        with open('history.json', 'w', encoding='utf-8') as f:
            json.dump(self.all_posts, f)

    # 新增运单
    def add_post(self, event=NONE):
        if self.post_id_var.get() == '':
            return
        if self.post_company_name_var.get() == '':
            try:
                with urllib.request.urlopen(self.auto_company_url + self.post_id_var.get()) as response:
                    company_code = json.loads(response.read().decode())['auto'][0]['comCode']
            except IndexError:
                return
        else:
            company_code = self.company_codes[self.post_company_name_var.get()]

        post = {'post_id': self.post_id_var.get(), 'company_code': company_code,
                'company_name': self.company_names[company_code], 'note': self.post_note_var.get()}
        self.all_posts[self.post_id_var.get()] = post
        self.posts.insert('', 0, self.post_id_var.get(), text='%s' % self.post_id_var.get())  # 将单号加入列表
        self.update_post_detail(post)
        self.posts.selection_set(self.post_id_var.get())
        self.save_history()

        # 清空输入框
        self.post_id_var.set('')
        self.post_note_var.set('')
        self.post_company_name_var.set('')
        self.post_id_field.focus_set()

    # 移除运单
    def remove_post(self, event=NONE):
        self.all_posts.pop(self.posts.selection()[0])
        self.posts.delete(self.posts.selection()[0])
        self.post_detail.config(state=NORMAL)
        self.post_detail.delete('1.0', END)
        self.post_detail.config(state=DISABLED)
        self.save_history()

    # 更新全部运单动态
    def update_all_posts(self, event=NONE):
        for post in self.all_posts.values():
            self.update_post_detail(post)
        self.save_history()

    # 更新单个运单状态
    def update_post_detail(self, post=NONE):
        if post == NONE:
            post = self.all_posts[self.posts.selection()[0]]
        with urllib.request.urlopen(self.query_url + 'type=' + post['company_code'] + '&postid=' + post['post_id'])\
                as response:
            obj = json.loads(response.read().decode())
            self.all_posts[post['post_id']]['status'] = obj['status']
            if obj['status'] == '200':
                self.all_posts[post['post_id']]['data'] = obj['data']
                self.all_posts[post['post_id']]['state'] = obj['state']
                self.all_posts[post['post_id']]['last_update'] = obj['data'][0]['time']
            else:
                self.all_posts[post['post_id']]['data'] = [{'time': '快递公司参数异常',
                                                            'context': '单号不存在或者已经过期'}]
                self.all_posts[post['post_id']]['state'] = '-1'
                self.all_posts[post['post_id']]['last_update'] = ''
        self.posts.item(post['post_id'],
                        values=(post['note'], post['company_name'], self.state[post['state']], post['last_update']))

    # 显示运单详情
    def show_post_detail(self, event=NONE):
        self.post_detail.config(state=NORMAL)  # 允许编辑消息记录文本框
        self.post_detail.delete('1.0', END)
        for x in self.all_posts[self.posts.selection()[0]]['data']:
            self.post_detail.insert('end', x['time'] + '\t' + x['context'] + '\n')
        self.post_detail.config(state=DISABLED)  # 禁止编辑消息记录文本框

if __name__ == '__main__':
    root = Tk()
    app = ExpressQuery(root)
    root.mainloop()
