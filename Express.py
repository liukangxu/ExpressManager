import json
import tkinter
import threading
from urllib import request
from tkinter import N, E, S, W
from tkinter.scrolledtext import ScrolledText
from tkinter.ttk import *
from multiprocessing.dummy import Pool as ThreadPool


class ExpressQuery(Frame):
    def __init__(self, master):
        Frame.__init__(self, master)
        self.root = master
        self.root.bind_all('<F5>', self.update_all_posts)
        self.root.bind_all('<Escape>', self.clear_input)
        self.all_posts = {}  # 运单列表
        self.root.title('快递助手 v1.2')
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
        self.post_id_var = tkinter.StringVar()  # 运单号
        self.post_id_field = Entry(add_post_group, width=20, textvariable=self.post_id_var)
        self.post_id_field.bind('<Return>', self.handle_add_post)
        post_note_label = Label(add_post_group, text='备注:')
        self.post_note_var = tkinter.StringVar()  # 运单注释
        post_note_field = Entry(add_post_group, width=20, textvariable=self.post_note_var)
        post_note_field.bind('<Return>', self.handle_add_post)
        post_company_label = Label(add_post_group, text='公司：')
        self.post_company_name_var = tkinter.StringVar()
        self.post_company_field = Combobox(add_post_group, textvariable=self.post_company_name_var,
                                           values=list(self.company_names.values()), width=12)
        post_add_button = Button(add_post_group, text='添加', width=10, command=self.handle_add_post)
        clear_input_button = Button(add_post_group, text='清空', width=10, command=self.clear_input)

        post_id_label.grid(row=0, column=0)
        self.post_id_field.grid(row=0, column=1)
        post_note_label.grid(row=0, column=2)
        post_note_field.grid(row=0, column=3)
        post_company_label.grid(row=0, column=4)
        self.post_company_field.grid(row=0, column=5)
        post_add_button.grid(row=0, column=6, padx=5)
        clear_input_button.grid(row=0, column=7, padx=5)
        self.post_id_field.focus_set()

        show_posts_group = Frame(parent_frame)
        self.posts = Treeview(show_posts_group, height=10, selectmode='browse',
                              columns=('note', 'company_name', 'state', 'last_update'))  # 运单列表框
        self.x_scrollbar = Scrollbar(show_posts_group, orient=tkinter.HORIZONTAL, command=self.posts.xview)
        self.y_scrollbar = Scrollbar(show_posts_group, orient=tkinter.VERTICAL, command=self.posts.yview)
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
        self.post_detail = ScrolledText(show_posts_group, bg='white', width=92, height=16, state=tkinter.DISABLED)
        self.posts.grid(row=0, column=0, sticky=W + N + S)
        self.x_scrollbar.grid(row=1, column=0, sticky=E + W)
        self.y_scrollbar.grid(row=0, column=1, sticky=N + S)
        self.post_detail.grid(row=2, column=0, sticky=W + N + S, padx=(0, 10))
        status_label = Label(parent_frame, text='F5 更新全部运单动态')

        add_post_group.grid(row=0, column=0)
        show_posts_group.grid(row=1, column=0)
        status_label.grid(row=2, column=0)

        self.get_history()

    # 获取历史记录
    def get_history(self):
        try:
            with open('history.json', 'r', encoding='utf-8') as f:
                self.all_posts = json.loads(f.read())
            for post_id in self.all_posts:
                self.posts.insert('', 0, post_id,
                                  text=post_id,
                                  values=(self.all_posts[post_id]['note'],
                                          self.all_posts[post_id]['company_name'],
                                          self.state[self.all_posts[post_id]['state']],
                                          self.all_posts[post_id]['last_update']))
        except ValueError:
            with open('history.json', 'w', encoding='utf-8') as f:
                json.dump(self.all_posts, f)
            print('No history record found')

    # 保存运单记录
    def save_history(self):
        with open('history.json', 'w', encoding='utf-8') as f:
            json.dump(self.all_posts, f)

    # 新增运单
    def handle_add_post(self, event=None):
        if self.post_id_var.get() == '':
            return

        if self.post_company_name_var.get():
            company_code = self.company_codes[self.post_company_name_var.get()]
        else:
            try:
                with request.urlopen(self.auto_company_url + self.post_id_var.get()) as response:
                    company_code = json.loads(response.read().decode())['auto'][0]['comCode']
            except IndexError:
                return

        post = {
            'post_id': self.post_id_var.get(),
            'company_code': company_code,
            'company_name': self.company_names[company_code],
            'note': self.post_note_var.get()}

        self.all_posts[post['post_id']] = post

        try:
            self.posts.index(post['post_id'])
        except tkinter.TclError:
            self.posts.insert('', 0, self.post_id_var.get(), text='%s' % self.post_id_var.get())

        handle_add_post = threading.Thread(target=self.handle_add_post_thread, args=(post,))
        handle_add_post.start()

        self.clear_input()

    def handle_add_post_thread(self, post):
        self.update_post_detail_thread(post)
        self.posts.selection_set(post['post_id'])
        self.save_history()

    # 清空输入框
    def clear_input(self, event=None):
        self.post_id_var.set('')
        self.post_note_var.set('')
        self.post_company_name_var.set('')
        self.post_id_field.focus_set()

    # 移除运单
    def remove_post(self, event=None):
        self.all_posts.pop(self.posts.selection()[0])
        self.posts.delete(self.posts.selection()[0])
        self.post_detail.config(state=tkinter.NORMAL)
        self.post_detail.delete('1.0', tkinter.END)
        self.post_detail.config(state=tkinter.DISABLED)
        self.save_history()
        self.clear_input()

    # 更新全部运单动态
    def update_all_posts(self, event=None):
        update_all_posts = threading.Thread(target=self.update_all_posts_thread)
        update_all_posts.start()

    def update_all_posts_thread(self):
        pool = ThreadPool(4)
        posts = list(self.all_posts.values())
        pool.map(self.update_post_detail, posts)
        pool.close()
        pool.join()
        self.save_history()

    # 更新单个运单状态
    def update_post_detail(self, post=None):
        update_post_detail  = threading.Thread(target=self.update_post_detail_thread)
        update_post_detail.start()

    def update_post_detail_thread(self, post=None):
        if not post:
            post = self.all_posts[self.posts.selection()[0]]
        with request.urlopen(self.query_url + 'type=' + post['company_code'] + '&postid=' + post['post_id'])\
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
    def show_post_detail(self, event=None):
        selected_post = self.all_posts[self.posts.selection()[0]]
        self.post_id_var.set(selected_post['post_id'])
        self.post_note_var.set(selected_post['note'])
        self.post_company_name_var.set(selected_post['company_name'])

        self.post_detail.config(state=tkinter.NORMAL)  # 允许编辑消息记录文本框
        self.post_detail.delete('1.0', tkinter.END)
        for x in selected_post['data']:
            self.post_detail.insert('end', x['time'] + '\t' + x['context'] + '\n')
        self.post_detail.config(state=tkinter.DISABLED)  # 禁止编辑消息记录文本框

if __name__ == '__main__':
    root = tkinter.Tk()
    app = ExpressQuery(root)
    root.mainloop()
