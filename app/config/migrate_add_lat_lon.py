-- 为摄像头表添加经纬度字段
-- 执行前请备份数据库

ALTER TABLE camera_info ADD COLUMN latitude FLOAT NULL;
ALTER TABLE camera_info ADD COLUMN longitude FLOAT NULL;
