from tkinter import *
import re
from hashlib import md5
from tkinter.ttk import *
from tkinter import font,colorchooser,filedialog,messagebox
import os
import tempfile

root =Tk()
root.option_add("*Font", ('Helvetica', 14))
root.title("text editor")
root.geometry("1200x730+10+10")
#root.resizable(False,False)

nb= Notebook(root)
nb.place(x=10,y=65)

def current_tab():
        return nb.nametowidget(nb.select() )

def indexed_tab(index):
        return nb.nametowidget( nb.tabs()[index] )

    # Move tab position by dragging tab
def move_tab(event):
    if nb.index("end") > 1:
        y = current_tab().winfo_y() - 5
        try:
            nb.insert( min( event.widget.index('@%d,%d' % (event.x, y)), nb.index('end')-2), nb.select() )
        except TclError:
            pass


def open_file(*args):        
    # Open a window to browse to the file you would like to open, returns the directory.
    global file_dir
    file_dir = (filedialog.askopenfilename(initialdir=init_dir, title="Select file", filetypes=filetypes))
        
    # If directory is not the empty string, try to open the file. 
    if file_dir:
        try:
            # Open the file.
            file = open(file_dir)  
            # Create a new tab and insert at end.
            new_tab = Tab(FileDir=file_dir)
            nb.insert( nb.index('end')-1, new_tab, text=os.path.basename(file_dir))
            nb.select( new_tab )               
            # Puts the contents of the file into the text widget.
            current_tab().textbox.insert('end', file.read())     
            # Update hash
            current_tab().status = md5(current_tab().textbox.get(1.0, 'end').encode('utf-8'))
        except:
            return

def save_as():
    curr_tab = current_tab()
    # Gets file directory and name of file to save.
    file_dir = (filedialog.asksaveasfilename(initialdir=init_dir, title="Select file", filetypes=filetypes, defaultextension='.txt'))
        
    # Return if directory is still empty (user closes window without specifying file name).
    if not file_dir:
        return     
     # Adds .txt suffix if not already included.
    if file_dir[-4:] != '.txt':
        file_dir += '.txt'    
    curr_tab.file_dir = file_dir
    curr_tab.file_name = os.path.basename(file_dir)
    nb.tab( curr_tab, text=curr_tab.file_name)
            
     # Writes text widget's contents to file.
    file = open(file_dir, 'w')
    file.write(curr_tab.textbox.get(1.0, 'end'))
    file.close()
     # Update hash
    curr_tab.status = md5(curr_tab.textbox.get(1.0, 'end').encode('utf-8'))
        
def save_file():
    curr_tab = current_tab()
        # If file directory is empty or Untitled, use save_as to get save information from user. 
    if not curr_tab.file_dir:
        save_as()
        # Otherwise save file to directory, overwriting existing file or creating a new one.
    else:
        with open(curr_tab.file_dir, 'w') as file:
            file.write(curr_tab.textbox.get(1.0, 'end'))     
        # Update hash
        curr_tab.status = md5(curr_tab.textbox.get(1.0, 'end').encode('utf-8'))
                
def new_file():                
     # Create new tab
    new_tab = Tab(FileDir=default_filename())
    new_tab.textbox.config(wrap= 'word' if word_wrap.get() else 'none')
    nb.insert( nb.index('end')-1, new_tab, text=new_tab.file_name)
    nb.select( new_tab )
        
def copy():
        # Clears the clipboard, copies selected contents.
    try: 
        sel = current_tab().textbox.get(SEL_FIRST, SEL_LAST)
        root.clipboard_clear()
        root.clipboard_append(sel)
        # If no text is selected.
    except TclError:
        pass
            
def delete():
        # Delete the selected text.
    try:
        current_tab().textbox.delete(SEL_FIRST, SEL_LAST)
        # If no text is selected.
    except TclError:
        pass
            
def cut():
        # Copies selection to the clipboard, then deletes selection.
    try: 
        sel = current_tab().textbox.get(SEL_FIRST, SEL_LAST)
        #print("bjbd",sel)
        root.clipboard_clear()
        root.clipboard_append(sel)
        current_tab().textbox.delete(SEL_FIRST, SEL_LAST)
        # If no text is selected.
    except TclError:
        pass
            
def wrap():
    if word_wrap.get() == True:
        for i in range(nb.index('end')-1):
            indexed_tab(i).textbox.config(wrap="word")
    else:
        for i in range(nb.index('end')-1):
            indexed_tab(i).textbox.config(wrap="none")
            
def paste():
    try: 
        current_tab().textbox.insert(INSERT, root.clipboard_get())
    except TclError:
        pass
            
def select_all( *args):
    curr_tab = current_tab()
        # Selects / highlights all the text.
    curr_tab.textbox.tag_add(SEL, "1.0", END) 
        # Set mark position to the end and scroll to the end of selection.
    curr_tab.textbox.mark_set(INSERT, END)
    curr_tab.textbox.see(INSERT)

def undo():
    current_tab().textbox.edit_undo()

def right_click(event):
    right_click_menu.post(event.x_root, event.y_root)
        
def right_click_tab(event):
    tab_right_click_menu.post(event.x_root, event.y_root)

def close_tab( event=None):
        # Close the current tab if close is selected from file menu, or keyboard shortcut.
    if event is None or event.type == str( 2 ):
        selected_tab =nb.current_tab()
        # Otherwise close the tab based on coordinates of center-click.
    else:
        try:
            index = event.widget.index('@%d,%d' % (event.x, event.y))
            selected_tab =nb.indexed_tab( index )        
            if index == nb.index('end')-1:
                return
        except TclError:
            return
        # Prompt to save changes before closing tab
    if save_changes(selected_tab):
            # if the tab next to '+' is selected, select the previous tab to prevent
            # automatically switching to '+' tab when current tab is closed
        if nb.index('current') > 0 and nb.select() == nb.tabs()[-2]:
            nb.select(nb.index('current')-1)
        nb.forget( selected_tab )
        # Exit if last tab is closed
    if nb.index("end") <= 1:
        root.destroy()
        
def exit():        
        # Check if any changes have been made.
        # TODO: Check all tabs for changes, not just current one
    if save_changes(current_tab()):
        root.destroy()
    else:
        return
               
def save_changes(tab):
        # Check if any changes have been made, returns False if user chooses to cancel rather than select to save or not.
    if md5(tab.textbox.get(1.0, 'end').encode('utf-8')).digest() != tab.status.digest():
            # Select the tab being closed is not the current tab, select it.
        if current_tab() != tab:
            nb.select(tab)
            # If changes were made since last save, ask if user wants to save.
        m = messagebox.askyesnocancel('Editor', 'Do you want to save changes to ' + tab.file_dir + '?' )     
            # If None, cancel.
        if m is None:
            return False
            # else if True, save.
        elif m is True:
            save_file()
            # else don't save.
        else:
            pass            
    return True

def default_filename():
    global untitled_count
    untitled_count += 1
    return 'Untitled' + str(untitled_count-1)

def tab_change(event):
    # If last tab was selected, create new tab
    if nb.select() == nb.tabs()[-1]:
        new_file()
        
def find():
    def find_words():
        textbox.tag_remove("match",1.0,END)
        start_pos="1.0"
        word=findentryField.get()
        if word:
            while True:
                start_pos=textbox.search(word,start_pos,stopindex=END)
                if not start_pos:
                    break
                end_pos=f"{start_pos}+{len(word)}c"
                textbox.tag_add("match",start_pos,end_pos)
                textbox.tag_config("match",background="yellow",foreground="red")
                start_pos=end_pos
                
    def replace_text():
        word=findentryField.get()
        replaceword=replaceentryField.get()
        content=textbox.get(1.0,END)
        new_content=content.replace(word,replaceword)
        textbox.delete(1.0,END)
        textbox.insert(1.0,new_content)
        
    root1=Toplevel()
    root1.title("Find")
    root1.geometry("380x190+500+200")
    root1.resizable(0,0)
    
    labelFrame=LabelFrame(root1,text="Find/Replace")
    labelFrame.pack(pady=20)
    
    findLabel=Label(labelFrame,text="Find")
    findLabel.grid(row=0,column=0,padx=8,pady=8)
    
    findentryField=Entry(labelFrame)
    findentryField.grid(row=0,column=1,padx=8,pady=8)
    
    replaceLabel=Label(labelFrame,text="Replace")
    replaceLabel.grid(row=1,column=0,padx=8,pady=8)
    replaceentryField=Entry(labelFrame)
    replaceentryField.grid(row=1,column=1,padx=8,pady=8)
    
    findButton=Button(labelFrame,text="FIND",command=find_words)
    findButton.grid(row=2,column=0,padx=10,pady=8)
    
    replaceButton=Button(labelFrame,text="REPLACE",command=replace_text)
    replaceButton.grid(row=2,column=1,padx=10,pady=8)
    
    def doSomething():
        textbox.tag_remove("match",1.0,END)
        root1.destroy()
        
    root1.protocol("WM_DELETE_WINDOW",doSomething)
    root1.mainloop()
    
   
#========================================================================================================================[[[]]]
class Tab(Frame):
    def __init__(self, *args, FileDir):
        Frame.__init__(self, *args)
        self.textbox = self.create_text_widget()
        self.file_dir = FileDir
        self.file_name = os.path.basename(FileDir)
        self.status = md5(self.textbox.get(1.0, 'end').encode('utf-8'))
        
    def create_text_widget(self):
        global textbox
        # Horizontal Scroll Bar
        xscrollbar =Scrollbar(self, orient='horizontal',)
        xscrollbar.pack(side='bottom', fill='x')

        # Vertical Scroll Bar
        yscrollbar = Scrollbar(self)
        yscrollbar.pack(side='right', fill='y')

        # Create Text Editor Box
        textbox = Text(self, relief='sunken', borderwidth=0, wrap='none')
        textbox.config(xscrollcommand=xscrollbar.set, yscrollcommand=yscrollbar.set, undo=True, autoseparators=True,width=105)
        
        # Pack the textbox
        textbox.pack(fill='both', expand=True)

        # Configure Scrollbars
        xscrollbar.config(command=textbox.xview)
        yscrollbar.config(command=textbox.yview)

        return textbox
    

def change_bgcolor(bg_color,fg_color):
    textbox.configure(bg=bg_color,fg=fg_color)

#=================================================================================================
fontSize=12
fontStyle="arial"

def font_style(event):
    global fontStyle
    fontStyle=font_family_variable.get()
    
    for i in range(nb.index('end')-1):
            indexed_tab(i).textbox.config(font=(fontStyle,fontSize))
  
  
    
def font_size(event):
    global fontSize
    #sel = current_tab().textbox.get(SEL_FIRST, SEL_LAST)
    
    fontSize=size_variable.get()
    for i in range(nb.index('end')-1):
            indexed_tab(i).textbox.config(font=(fontStyle,fontSize))


#======================================================================================================
menubar = Menu(root)
filemenu = Menu(menubar, tearoff=0,font=("helvetica 12"))

newImage=PhotoImage(file="img/new.png")
openImage=PhotoImage(file="img/open.png")
saveImage=PhotoImage(file="img/saveas.png")
saveasImage=PhotoImage(file="img/save.png")
exitImage=PhotoImage(file="img/exit.png")
printImage=PhotoImage(file="img/print.png")
filemenu.add_command(label=" New",accelerator="Ctrl+N",image=newImage,compound=LEFT,command=new_file)
filemenu.add_command(label=" Open",accelerator="Ctrl+O",image=openImage,compound=LEFT,command=open_file)
filemenu.add_command(label=" Save",accelerator="Ctrl+S",image=saveImage,compound=LEFT,command=save_file)
filemenu.add_command(label=" Save As",accelerator="Ctrl+Alt+S",image=saveasImage,compound=LEFT,command=save_as)
filemenu.add_command(label=" Close",accelerator="Ctrl+P",image=printImage,compound=LEFT,command=close_tab)
filemenu.add_separator()
filemenu.add_command(label="Exit",accelerator="Ctrl+Q",image=exitImage,compound=LEFT,command=exit)

        
# Create Edit Menu
editmenu = Menu(menubar, tearoff=0)


cutImage=PhotoImage(file="img/cut.png")
copyImage=PhotoImage(file="img/copy.png")
pasteImage=PhotoImage(file="img/paste.png")
clearImage=PhotoImage(file="img/clear.png")
findImage=PhotoImage(file="img/find.png")
selectImage=PhotoImage(file="img/select.png")
undoImage=PhotoImage(file="img/undo.png")

editmenu.add_command(label=" Undo",accelerator="Ctrl+Z",image=undoImage,compound=LEFT,command=undo)
editmenu.add_separator()
editmenu.add_command(label=" Cut",accelerator="Ctrl+X",image=cutImage,compound=LEFT,command=cut)
editmenu.add_command(label=" Copy",accelerator="Ctr+C",image=copyImage,compound=LEFT,command=copy)
editmenu.add_command(label=" Paste",accelerator="Ctrl+V",image=pasteImage,compound=LEFT,command=paste)
editmenu.add_command(label=" Select All",accelerator="Ctrl+A",image=selectImage,compound=LEFT,command=select_all)

editmenu.add_command(label=" Clear",accelerator="Ctrl+Alt+X",image=clearImage,compound=LEFT,command=delete)
editmenu.add_command(label=" Find",accelerator="Ctrl+F",image=findImage,compound=LEFT,command=find)
       
# Create Format Menu, with a check button for word wrap.
formatmenu = Menu(menubar, tearoff=0,font="helvetica 13")
word_wrap = BooleanVar()
formatmenu.add_checkbutton(label="Word Wrap", onvalue=True, offvalue=False, variable=word_wrap, command=wrap)
        
menubar.add_cascade(label="File", menu=filemenu)
menubar.add_cascade(label="Edit", menu=editmenu)
menubar.add_cascade(label="Format", menu=formatmenu)
root.config(menu=menubar)


# Create right-click menu.
right_click_menu = Menu(root, tearoff=0)
right_click_menu.add_command(label="Undo", command=undo)
right_click_menu.add_separator()
right_click_menu.add_command(label="Cut", command=cut)
right_click_menu.add_command(label="Copy", command=copy)
right_click_menu.add_command(label="Paste", command=paste)
right_click_menu.add_command(label="Delete", command=delete)
right_click_menu.add_separator()
right_click_menu.add_command(label="Select All", command=select_all)
        
# Create tab right-click menu
tab_right_click_menu = Menu(nb, tearoff=0)
tab_right_click_menu.add_command(label="New Tab", command=new_file)


themesmenu=Menu(menubar,tearoff=False,font="Helvetica 13 ")
menubar.add_cascade(label="Themes",menu=themesmenu)

lightImage=PhotoImage(file="img/light.png")
darkImage=PhotoImage(file="img/dark.png")
pinkImage=PhotoImage(file="img/pink.png")
blueImage=PhotoImage(file="img/blue.png")
yellowImage=PhotoImage(file="img/yellow.png")
#file_dir = (filedialog.askopenfilename(initialdir=init_dir, title="Select file", filetypes=filetypes))newTab=Tab(FileDir=(filedialog.askopenfilename(initialdir=init_dir, title="Select file", filetypes=filetypes)))
  
theme_choice=StringVar()
themesmenu.add_radiobutton(label=" Light Default",image=lightImage,variable=theme_choice,compound=LEFT,command=lambda:change_bgcolor("white","black"))
themesmenu.add_radiobutton(label=" Dark",image=darkImage,variable=theme_choice,compound=LEFT,command=lambda:change_bgcolor("black","white"))
themesmenu.add_radiobutton(label=" Pink",image=pinkImage,variable=theme_choice,compound=LEFT,command=lambda:change_bgcolor("#FDA9CD","black"))
themesmenu.add_radiobutton(label=" Blue",image=blueImage,variable=theme_choice,compound=LEFT,command=lambda:change_bgcolor("#57D3FF","black"))
themesmenu.add_radiobutton(label=" Yellow",image=yellowImage,variable=theme_choice,compound=LEFT,command=lambda:change_bgcolor("#FFD44B","black"))

        # Keyboard / Click Bindings
root.bind_class('Text', '<Control-s>', save_file)
root.bind_class('Text', '<Control-o>', open_file)
root.bind_class('Text', '<Control-n>', new_file)
root.bind_class('Text', '<Control-a>', select_all)
root.bind_class('Text', '<Control-w>', close_tab)
root.bind_class('Text', '<Button-3>', right_click)

#=============================================================================================================
#toolbarsection
tool_option=Label(root)
tool_option.pack(side=TOP,fill=X)

#fontfamily
font_families=font.families()
font_family_variable=StringVar()

fontfamily_Combobox=Combobox(tool_option,width=30,font="helvetica 13",values=font_families,state="readonly",textvariable=font_family_variable)
fontfamily_Combobox.current(font_families.index("Arial"))
fontfamily_Combobox.grid(row=0,column=0,padx=5,pady=10)

fontfamily_Combobox.bind("<<ComboboxSelected>>",font_style)


#fontsize
size_variable=StringVar()
font_size_Combobox=Combobox(tool_option,width=14,textvariable=size_variable,state="readonly",values=tuple(range(8,80)))
font_size_Combobox.current(4)
font_size_Combobox.grid(row=0,column=1,padx=5)

font_size_Combobox.bind("<<ComboboxSelected>>",font_size)

nb.enable_traversal()
nb.bind("<B1-Motion>",move_tab)


filetypes = (("Normal text file", "*.txt"), ("all files", "*.*"))
init_dir = os.path.join(os.path.expanduser('~'), 'Desktop')
untitled_count = 1
        
        # Create Noteb
nb.add(Tab(FileDir='Untitled'), text='Untitled')
nb.add(Tab(FileDir='f'), text=' + ')

nb.bind("<Button-2>", close_tab)
nb.bind('<<NotebookTabChanged>>',tab_change)
nb.bind('<Button-3>', right_click_tab)

root.protocol('WM_DELETE_WINDOW', exit)




root.mainloop()