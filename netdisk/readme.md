# A Simple WebDisk

### TODO
- [ ] 评论系统
- [ ] UI/UX improvement
> 大概照着这么抄
> ![](https://pbs.twimg.com/media/E-R_i3VVkAMGUQO?format=jpg&name=4096x4096)

### 一些想法和思路
- 伪文件系统是否需要垃圾回收机制？
- 伪文件系统如果某目录下有文件但是没有表示这个目录的文件怎么办？
- 如何保证单目录下文件唯一？

### 目前待做
- 审核流程（上传到oss）
- 页面内的排序（暂时🐦了）
- Anti-abuse: 记录log，限制单账号固定时间下载数量