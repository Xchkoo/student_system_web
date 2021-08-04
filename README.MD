1. 结构
    - 人脸库
    -- 注册人脸
    -- 查看人脸库
    -- 搜索

    - 签到
    -- 图片上传
    -- 查询

    - OCR
    -- 上传图片
    -- 查询

    - 课堂拍照
    -- 拍照
    -- 查询

2. 本地搭建方法
    - 推荐: 使用docker image 导入项目
    修改app_mask/config.py内的APP_PATH为你的本地环境目录。
    运行run.py后访问127.0.0.1，局域网访问本机ip。

3. 使用提示
    | 已知bug在issue里有解决方案。
    | 表格录入要保证头行是config.py内的is_commit_word之一，可修改is_commit_word。