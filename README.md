# aiooss_repair
最新版的oss2包和最新版的aiooss在response格式上有一点小出入，在这里修复

版本
```
aiooss (0.1.2)
oss2 (2.7.0)
```

问题：
虽然aiooss把调用方法变成异步执行，但是resp的验证是调用的oss2里面的models.PutObjectResult方法，会验证一个request_id的属性，但是aiooss里面没有带这个属性，通过对比oss2最新版和aiooss的最新版发现是aiooss少些一个类，把这个类加上就好了
