Traceback (most recent call last):
  File "D:\python\lolssh.py", line 94, in <module>
    main()
  File "D:\python\lolssh.py", line 88, in main
    display_menu(root, client, 'ls -1', log_window, True)
  File "D:\python\lolssh.py", line 51, in display_menu
    data = execute_command(client, command, log_window)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\python\lolssh.py", line 32, in execute_command
    log_window.insert(tk.END, f"Commande exécutée : {command}\n")
  File "C:\Users\MegaZBuro\AppData\Local\Programs\Python\Python312\Lib\tkinter\__init__.py", line 3842, in insert
    self.tk.call((self._w, 'insert', index, chars) + args)
_tkinter.TclError: invalid command name ".!frame.!scrolledtext"