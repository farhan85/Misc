" Save this file at $HOME/.vimrc
" This file uses Vundle to manage plugins


set nocompatible  " Use Vim settings (instead of Vi settings)

set rtp+=~/.vim/bundle/vundle
filetype off  " required by vundle
call vundle#begin()

" To install a plugin, add it to this list, then run :PluginInstall
Plugin 'gmarik/vundle'
Plugin 'scrooloose/nerdtree'
Plugin 'vim-airline/vim-airline'
Plugin 'vim-airline/vim-airline-themes'
Plugin 'vim-python/python-syntax'

call vundle#end()


" Enable filetype detection, load plugin files for specific filetypes, and
" indent files for specific filetypes
filetype plugin indent on


set encoding=utf-8
set t_Co=256                    " Enable 256 colors in vim
set autoindent                  " Indent at same length as previous line
set background=dark             " I don't want to be blinded by my screen
set cursorline                  " Show the current line the cursor is on
set number                      " Show line numbers
set relativenumber              " Display relative line numbers
set nowrap                      " No wordwrap
set showcmd                     " Show the commands you are typing
set backspace=indent,eol,start  " Make backspace work like most other apps
set expandtab                   " Use spaces instead of TABs
set smarttab                    " Use spaces instead TABs at start of lines
set ruler                       " Show character/column count, for current line, at the bottom of the screen
set showmatch                   " Show matching brackets/parentheses
set laststatus=2                " Make sure the status bar is also displayed when a single file is open


" Buffers
set hidden   " Allow buffers to be hidden when switching between them
set confirm  " But Vim must confirm you want to close a buffer with unsaved changes


" Searching
set ignorecase  " Ignore case when searching
set smartcase   " But if there are captial letters, then make it case sensitive
set incsearch   " Use incremental search
set hlsearch    " And highlight as we search


" 8 character indent is so ugly
set tabstop=4      " Width of TAB
set softtabstop=4  " Number of columns for a TAB
set shiftwidth=4   " Width of indents

" Filetypes that I want to use tabsize of size 2
autocmd FileType ruby setlocal tabstop=2 softtabstop=2 shiftwidth=2
autocmd FileType html setlocal tabstop=2 softtabstop=2 shiftwidth=2

" Makefiles need to use actual TABs
autocmd FileType make setlocal tabstop=4 softtabstop=0 shiftwidth=4 noexpandtab nosmarttab

" Autoindent is not needed when pasting large amounts of text.
" Set a toggle to easily turn it on/off
set pastetoggle=<F12>


" Automatically wrap git commit messages
au FileType gitcommit set tw=72


" Indicate the range of columns that are too far out
" e.g. indicate the 80th column for PEP8
"execute "set colorcolumn=" . join(range(81,335), ',')
set colorcolumn=81


" Use syntax highlighting
syntax enable
"colorscheme solarized
"colorscheme hybrid
colorscheme PaperColor


" Airline config
"let g:airline_theme = 'solarized'
"let g:airline_theme = 'badwolf'
let g:airline_theme = 'serene'
let g:airline_powerline_fonts = 1
let g:airline#extensions#tabline#enabled = 1
let g:airline#extensions#tabline#buffer_nr_show = 1

" Python-syntax config
"let g:python_highlight_all = 1
let g:python_highlight_func_calls = 1
let g:python_highlight_indent_errors = 1
let g:python_highlight_space_errors = 1
let g:python_highlight_file_headers_as_comments = 1
let g:python_highlight_exceptions = 1
let g:python_highlight_builtins = 1
let g:python_highlight_operators = 1
let g:python_highlight_class_vars = 1

" NERDTree config
map <F2> :NERDTreeToggle<CR>
map <C-n> :NERDTree<CR>

" Ctags
"set tags=./tags;
