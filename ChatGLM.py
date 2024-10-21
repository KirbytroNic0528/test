# 指定文件名和路径  
filename = "example.txt"  
  
# 使用 'w' 模式打开文件，该模式会创建一个新文件，如果文件已存在则会覆盖  
with open(filename, 'w') as file:  
    # 写入一些内容到文件  
    file.write("这是一个新创建的文件。\n")  
    file.write("11111111111111")  
  
print(f"{filename} 已成功创建。")
