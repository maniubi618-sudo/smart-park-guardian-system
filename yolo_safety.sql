/*
 Navicat Premium Dump SQL

 Source Server         : localhost_3306
 Source Server Type    : MySQL
 Source Server Version : 80012 (8.0.12)
 Source Host           : localhost:3306
 Source Schema         : yolo_safety

 Target Server Type    : MySQL
 Target Server Version : 80012 (8.0.12)
 File Encoding         : 65001

 Date: 20/05/2026 13:25:47
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for alarm
-- ----------------------------
DROP TABLE IF EXISTS `alarm`;
CREATE TABLE `alarm`  (
  `alarm_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `camera_id` int(11) NOT NULL,
  `alarm_type` tinyint(4) NOT NULL COMMENT '0-安全规范（未戴安全帽/未穿反光衣） 1-区域入侵（人/车） 2-火警（火焰/烟雾）',
  `alarm_status` tinyint(4) NOT NULL DEFAULT 0 COMMENT '0-未处理 1-确认误报 2-处理中（已派单） 3-处理完成',
  `alarm_time` datetime NOT NULL,
  `snapshot_url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `create_time` datetime NULL DEFAULT NULL,
  `update_time` datetime NULL DEFAULT NULL,
  `alarm_end_time` datetime NULL DEFAULT NULL,
  PRIMARY KEY (`alarm_id`) USING BTREE,
  INDEX `ix_alarm_alarm_id`(`alarm_id` ASC) USING BTREE,
  INDEX `ix_alarm_camera_id`(`camera_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 57 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of alarm
-- ----------------------------
INSERT INTO `alarm` VALUES (1, 1, 0, 3, '2024-02-01 08:30:00', '/snapshots/alarm1.jpg', '2024-02-01 08:30:00', '2024-02-01 09:15:00', NULL);
INSERT INTO `alarm` VALUES (2, 2, 0, 3, '2024-02-01 09:45:00', '/snapshots/alarm2.jpg', '2024-02-01 09:45:00', '2024-02-01 10:30:00', NULL);
INSERT INTO `alarm` VALUES (3, 3, 2, 1, '2024-02-01 10:15:00', '/snapshots/alarm3.jpg', '2024-02-01 10:15:00', '2024-02-01 10:20:00', NULL);
INSERT INTO `alarm` VALUES (4, 4, 2, 2, '2024-02-01 14:20:00', '/snapshots/alarm4.jpg', '2024-02-01 14:20:00', '2024-02-01 14:25:00', NULL);
INSERT INTO `alarm` VALUES (5, 1, 2, 0, '2024-02-01 15:50:00', '/snapshots/alarm5.jpg', '2024-02-01 15:50:00', '2024-02-01 15:50:00', NULL);
INSERT INTO `alarm` VALUES (37, 6, 0, 0, '2025-09-18 16:38:48', 'https://yolo-park-safety-guard.oss-cn-beijing.aliyuncs.com/6_2025-09-18 16:38:46.jpg', '2025-09-18 16:38:38', '2025-09-18 16:38:38', NULL);
INSERT INTO `alarm` VALUES (38, 1, 1, 0, '2025-09-25 11:14:59', 'https://yolo-park-safety-guard.oss-cn-beijing.aliyuncs.com/2025/09/25/e93a17a5-30d8-4464-aa79-bcf3d05576ee.jpg', '2025-09-25 11:13:35', '2025-09-25 11:13:35', NULL);
INSERT INTO `alarm` VALUES (39, 3, 1, 0, '2025-09-25 13:53:41', 'https://yolo-park-safety-guard.oss-cn-beijing.aliyuncs.com/2025/09/25/32da11e0-d646-441f-9270-224a09f68d6d.jpg', '2025-09-25 13:53:02', '2025-09-25 13:53:02', NULL);
INSERT INTO `alarm` VALUES (40, 2, 0, 0, '2025-10-21 14:19:35', 'https://yolo-park-safety-guard.oss-cn-beijing.aliyuncs.com/2025/10/21/8f7a368f-a71d-4ce1-bcbb-895a2fac3fba.jpg', '2025-10-21 14:16:58', '2025-10-21 14:16:58', NULL);
INSERT INTO `alarm` VALUES (41, 2, 0, 0, '2025-10-21 14:33:13', 'https://yolo-park-safety-guard.oss-cn-beijing.aliyuncs.com/2025/10/21/dffc764a-ff2f-4a18-9759-c1d135a04ffb.jpghttps://yolo-park-safety-guard.oss-cn-beijing.aliyuncs.com/2025/10/21/7ae6d0c8-f551-44dc-a303-e43e4c7da8c9.jpg,', '2025-10-21 14:32:40', '2025-10-21 14:32:40', NULL);
INSERT INTO `alarm` VALUES (42, 4, 2, 0, '2025-10-21 14:53:00', 'https://yolo-park-safety-guard.oss-cn-beijing.aliyuncs.com/2025/10/21/053c913f-a36c-4d0f-923f-8ebe7bc72e78.jpg', '2025-10-21 14:50:59', '2025-10-21 14:53:04', '2025-10-21 14:53:04');
INSERT INTO `alarm` VALUES (43, 4, 2, 0, '2025-10-21 14:53:16', 'https://yolo-park-safety-guard.oss-cn-beijing.aliyuncs.com/2025/10/21/8be27441-d3ff-4d70-8dcd-e6a6bedc2b50.jpg', '2025-10-21 14:50:59', '2025-10-21 14:53:22', '2025-10-21 14:53:22');
INSERT INTO `alarm` VALUES (44, 4, 2, 0, '2025-10-21 14:54:10', 'https://yolo-park-safety-guard.oss-cn-beijing.aliyuncs.com/2025/10/21/a6c1ce9c-ea64-4fd5-8dfd-d55277199fad.jpg', '2025-10-21 14:50:59', '2025-10-21 14:54:31', '2025-10-21 14:54:31');
INSERT INTO `alarm` VALUES (45, 4, 2, 0, '2025-10-21 14:55:07', 'https://yolo-park-safety-guard.oss-cn-beijing.aliyuncs.com/2025/10/21/6a4b8a3d-4194-469d-92c9-f2f6c7337291.jpg', '2025-10-21 14:50:59', '2025-10-21 14:55:09', '2025-10-21 14:55:09');
INSERT INTO `alarm` VALUES (46, 4, 2, 0, '2025-10-21 14:55:21', 'https://yolo-park-safety-guard.oss-cn-beijing.aliyuncs.com/2025/10/21/821865db-33e3-4f06-a7b1-9764e01c2c6f.jpg', '2025-10-21 14:50:59', '2025-10-21 14:50:59', NULL);
INSERT INTO `alarm` VALUES (47, 3, 1, 0, '2025-10-21 14:57:09', 'https://yolo-park-safety-guard.oss-cn-beijing.aliyuncs.com/2025/10/21/7ec9edca-ffa8-41fd-a5b0-76728f700307.jpg', '2025-10-21 14:56:41', '2025-10-21 14:56:41', NULL);
INSERT INTO `alarm` VALUES (48, 2, 0, 0, '2025-10-21 17:22:40', 'https://yolo-park-safety-guard.oss-cn-beijing.aliyuncs.com/2025/10/21/9060652d-21da-4a7b-b787-0f46ac5fe467.jpg', '2025-10-21 17:22:11', '2025-10-21 17:22:11', NULL);
INSERT INTO `alarm` VALUES (49, 2, 0, 0, '2025-10-21 19:07:12', 'https://yolo-park-safety-guard.oss-cn-beijing.aliyuncs.com/2025/10/21/e692fabc-4859-476d-9653-8705f5e26843.jpg', '2025-10-21 19:06:59', '2025-10-21 19:06:59', NULL);
INSERT INTO `alarm` VALUES (50, 2, 0, 0, '2025-10-21 19:13:13', 'https://yolo-park-safety-guard.oss-cn-beijing.aliyuncs.com/2025/10/21/0c5de948-9f23-4d20-ad6e-6bc3bedc4df0.jpg', '2025-10-21 19:08:18', '2025-10-21 19:08:18', NULL);
INSERT INTO `alarm` VALUES (51, 3, 1, 0, '2025-10-22 21:25:38', 'https://yolo-park-safety-guard.oss-cn-beijing.aliyuncs.com/2025/10/22/16657d25-398d-4e6f-acf5-07543856f5d9.jpg', '2025-10-22 21:01:19', '2025-10-22 21:01:19', NULL);
INSERT INTO `alarm` VALUES (52, 1, 1, 0, '2025-10-22 21:25:39', 'https://yolo-park-safety-guard.oss-cn-beijing.aliyuncs.com/2025/10/22/765ff021-0f69-4916-aec8-3f951e3e5808.jpg', '2025-10-22 21:01:19', '2025-10-22 21:25:54', '2025-10-22 21:25:54');
INSERT INTO `alarm` VALUES (53, 2, 0, 0, '2025-10-22 21:46:58', 'https://yolo-park-safety-guard.oss-cn-beijing.aliyuncs.com/2025/10/22/74af34b0-2014-432a-9c04-66fc1e691af5.jpg', '2025-10-22 21:01:19', '2025-10-22 21:01:19', NULL);
INSERT INTO `alarm` VALUES (54, 1, 1, 0, '2025-10-22 21:47:00', 'https://yolo-park-safety-guard.oss-cn-beijing.aliyuncs.com/2025/10/22/f6df28ca-2b7a-4f55-b6fa-8e514ae97018.jpg', '2025-10-22 21:01:19', '2025-10-22 21:47:38', '2025-10-22 21:47:38');
INSERT INTO `alarm` VALUES (55, 1, 1, 0, '2025-10-23 16:00:40', 'https://yolo-park-safety-guard.oss-cn-beijing.aliyuncs.com/2025/10/23/9c3e3193-4300-4b1d-aa0c-d7c72bb8d795.jpg', '2025-10-23 15:54:33', '2025-10-23 15:54:33', NULL);

-- ----------------------------
-- Table structure for alarm_handle_record
-- ----------------------------
DROP TABLE IF EXISTS `alarm_handle_record`;
CREATE TABLE `alarm_handle_record`  (
  `handle_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `alarm_id` bigint(20) NOT NULL,
  `handle_time` datetime NOT NULL,
  `handler_user_id` int(11) NOT NULL COMMENT '处理人 ID（系统用户），逻辑外键',
  `handle_action` int(11) NOT NULL COMMENT '处理动作：0-标记误报， 1-派单处理， 2-标记已解决',
  `handle_content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL,
  `handle_attachment_url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `create_time` datetime NULL DEFAULT NULL,
  `update_time` datetime NULL DEFAULT NULL,
  PRIMARY KEY (`handle_id`) USING BTREE,
  INDEX `ix_alarm_handle_record_handle_id`(`handle_id` ASC) USING BTREE,
  INDEX `ix_alarm_handle_record_alarm_id`(`alarm_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 8 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of alarm_handle_record
-- ----------------------------
INSERT INTO `alarm_handle_record` VALUES (1, 1, '2024-02-01 08:40:00', 2, 1, '派单给安保人员张三前往处理', NULL, '2024-02-01 08:40:00', '2024-02-01 08:40:00');
INSERT INTO `alarm_handle_record` VALUES (2, 1, '2024-02-01 09:15:00', 3, 2, '已提醒施工人员佩戴安全帽，现场照片见附件', '/attachments/alarm1_solved.jpg', '2024-02-01 09:15:00', '2024-02-01 09:15:00');
INSERT INTO `alarm_handle_record` VALUES (3, 2, '2024-02-01 09:50:00', 2, 1, '派单给仓库管理员李四处理', NULL, '2024-02-01 09:50:00', '2024-02-01 09:50:00');
INSERT INTO `alarm_handle_record` VALUES (4, 2, '2024-02-01 10:30:00', 4, 2, '已要求进入仓库人员穿戴反光衣', '/attachments/alarm2_solved.jpg', '2024-02-01 10:30:00', '2024-02-01 10:30:00');
INSERT INTO `alarm_handle_record` VALUES (5, 3, '2024-02-01 10:20:00', 1, 0, '经核实为误报，因摄像头角度偏移导致', NULL, '2024-02-01 10:20:00', '2024-02-01 10:20:00');
INSERT INTO `alarm_handle_record` VALUES (6, 4, '2024-02-01 14:25:00', 2, 1, '派单给消防巡查员王五紧急处理', NULL, '2024-02-01 14:25:00', '2024-02-01 14:25:00');

-- ----------------------------
-- Table structure for camera_info
-- ----------------------------
DROP TABLE IF EXISTS `camera_info`;
CREATE TABLE `camera_info`  (
  `camera_id` int(11) NOT NULL AUTO_INCREMENT,
  `camera_name` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `park_area_id` int(11) NOT NULL,
  `install_position` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `rtsp_url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `analysis_mode` int(11) NOT NULL,
  `camera_status` int(11) NULL DEFAULT NULL,
  `latitude` float NULL DEFAULT NULL,
  `longitude` float NULL DEFAULT NULL,
  `create_time` datetime NULL DEFAULT NULL,
  `update_time` datetime NULL DEFAULT NULL,
  PRIMARY KEY (`camera_id`) USING BTREE,
  INDEX `ix_camera_info_camera_id`(`camera_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 35 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of camera_info
-- ----------------------------
INSERT INTO `camera_info` VALUES (1, 'id为1的摄像头的新名字', 1, '东门岗亭上方', 'local:all.mp4', 1, 1, NULL, NULL, '2024-01-10 00:00:00', '2025-10-23 16:00:40');
INSERT INTO `camera_info` VALUES (2, '仓库区域摄像头', 2, '仓库门口', 'local:helmet_vest.mp4', 2, 1, NULL, NULL, '2024-01-10 00:00:00', '2025-10-22 21:46:52');
INSERT INTO `camera_info` VALUES (3, '危险品存放区摄像头', 3, '存放区围栏处', 'local:person_vehicle.mp4', 3, 1, NULL, NULL, '2024-01-10 00:00:00', '2025-10-22 21:52:00');
INSERT INTO `camera_info` VALUES (4, '消防通道摄像头', 1, '消防通道入口', 'local:fire_smoke.mp4', 4, 1, NULL, NULL, '2024-01-11 00:00:00', '2025-10-22 21:46:52');
INSERT INTO `camera_info` VALUES (5, '电梯轿厢摄像头', 3, '3号楼1单元电梯内', 'rtsp://192.168.1.106:554/stream', 1, 1, NULL, NULL, '2024-01-13 10:30:00', '2025-10-22 21:47:29');
INSERT INTO `camera_info` VALUES (6, '小区东门摄像头', 1, '东门岗亭外侧', 'rtsp://192.168.1.107:554/stream', 3, 1, NULL, NULL, '2024-01-14 14:00:00', '2025-10-22 21:48:18');
INSERT INTO `camera_info` VALUES (7, '地下车库摄像头', 2, '地下负一层拐角', 'rtsp://192.168.1.108:554/stream', 2, 1, NULL, NULL, '2024-01-15 09:15:00', '2025-10-22 21:48:53');
INSERT INTO `camera_info` VALUES (8, '单元门口摄像头', 3, '5号楼2单元门口', 'rtsp://192.168.1.109:554/stream', 1, 1, NULL, NULL, '2024-01-16 16:45:00', '2025-10-22 21:48:23');
INSERT INTO `camera_info` VALUES (9, '绿化带摄像头', 1, '中心花园北侧', 'rtsp://192.168.1.110:554/stream', 4, 1, NULL, NULL, '2024-01-17 11:20:00', '2025-10-22 21:26:15');
INSERT INTO `camera_info` VALUES (10, '垃圾站摄像头', 2, '生活垃圾站旁', 'rtsp://192.168.1.111:554/stream', 2, 1, NULL, NULL, '2024-01-18 07:30:00', '2025-10-22 21:26:15');
INSERT INTO `camera_info` VALUES (11, '健身区摄像头', 3, '室外健身器材区', 'rtsp://192.168.1.112:554/stream', 1, 1, NULL, NULL, '2024-01-19 15:50:00', '2025-10-22 21:26:15');
INSERT INTO `camera_info` VALUES (12, '物业办公室摄像头', 1, '物业前台内侧', 'rtsp://192.168.1.113:554/stream', 3, 1, NULL, NULL, '2024-01-20 13:10:00', '2025-10-22 21:26:15');
INSERT INTO `camera_info` VALUES (13, '快递柜摄像头', 2, '智能快递柜正面', 'rtsp://192.168.1.114:554/stream', 2, 1, NULL, NULL, '2024-01-21 10:05:00', '2025-10-22 21:26:15');
INSERT INTO `camera_info` VALUES (14, '儿童游乐区摄像头', 3, '滑梯旁', 'rtsp://192.168.1.115:554/stream', 1, 1, NULL, NULL, '2024-01-22 09:40:00', '2025-10-22 21:26:16');
INSERT INTO `camera_info` VALUES (15, '西门岗亭摄像头', 1, '西门岗亭内侧', 'rtsp://192.168.1.116:554/stream', 4, 1, NULL, NULL, '2024-01-23 16:25:00', '2025-10-22 21:26:16');
INSERT INTO `camera_info` VALUES (16, '水泵房摄像头', 2, '地下水泵房门口', 'rtsp://192.168.1.117:554/stream', 2, 1, NULL, NULL, '2024-01-24 14:50:00', '2025-10-22 21:26:16');
INSERT INTO `camera_info` VALUES (17, '配电房摄像头', 3, '配电房外侧', 'rtsp://192.168.1.118:554/stream', 1, 1, NULL, NULL, '2024-01-25 11:15:00', '2025-10-22 21:26:16');
INSERT INTO `camera_info` VALUES (18, '非机动车车库摄像头', 1, '非机动车出入口', 'rtsp://192.168.1.119:554/stream', 3, 1, NULL, NULL, '2024-01-26 08:30:00', '2025-10-22 21:26:16');
INSERT INTO `camera_info` VALUES (19, '监控中心摄像头', 2, '监控大屏前', 'rtsp://192.168.1.120:554/stream', 1, 1, NULL, NULL, '2024-01-27 15:40:00', '2025-10-22 21:26:15');
INSERT INTO `camera_info` VALUES (20, '会所大堂摄像头', 3, '会所入口处', 'rtsp://192.168.1.121:554/stream', 1, 1, NULL, NULL, '2024-01-28 12:20:00', '2025-10-22 21:26:15');
INSERT INTO `camera_info` VALUES (21, '消防控制室摄像头', 1, '消防控制操作台', 'rtsp://192.168.1.122:554/stream', 4, 1, NULL, NULL, '2024-01-29 10:50:00', '2025-10-22 21:26:16');
INSERT INTO `camera_info` VALUES (22, '南门入口摄像头', 2, '南门主通道', 'rtsp://192.168.1.123:554/stream', 2, 1, NULL, NULL, '2024-01-30 09:10:00', '2025-10-22 21:26:15');
INSERT INTO `camera_info` VALUES (23, '天台入口摄像头', 3, '10号楼天台门', 'rtsp://192.168.1.124:554/stream', 1, 1, NULL, NULL, '2024-01-31 17:30:00', '2025-10-22 21:26:15');
INSERT INTO `camera_info` VALUES (24, '垃圾分拣站摄像头', 1, '垃圾分类投放点', 'rtsp://192.168.1.125:554/stream', 3, 1, NULL, NULL, '2024-02-01 14:20:00', '2025-10-22 21:26:15');
INSERT INTO `camera_info` VALUES (25, '道闸系统摄像头', 2, '车辆道闸旁', 'rtsp://192.168.1.126:554/stream', 2, 1, NULL, NULL, '2024-02-02 11:45:00', '2025-10-22 21:26:15');
INSERT INTO `camera_info` VALUES (26, '电梯机房摄像头', 3, '电梯机房内', 'rtsp://192.168.1.127:554/stream', 1, 1, NULL, NULL, '2024-02-03 08:55:00', '2025-10-22 21:26:15');
INSERT INTO `camera_info` VALUES (27, '小区围墙摄像头', 1, '北侧围墙中段', 'rtsp://192.168.1.128:554/stream', 4, 1, NULL, NULL, '2024-02-04 16:10:00', '2025-10-22 21:26:15');
INSERT INTO `camera_info` VALUES (28, '商铺门口摄像头', 2, '沿街商铺前', 'rtsp://192.168.1.129:554/stream', 2, 1, NULL, NULL, '2024-02-05 13:30:00', '2025-10-22 21:26:15');
INSERT INTO `camera_info` VALUES (29, '活动中心摄像头', 3, '活动中心大厅', 'rtsp://192.168.1.130:554/stream', 1, 1, NULL, NULL, '2024-02-06 10:20:00', '2025-10-22 21:26:15');
INSERT INTO `camera_info` VALUES (30, '岗亭外侧摄像头', 1, '北门岗亭外部', 'rtsp://192.168.1.131:554/stream', 3, 1, NULL, NULL, '2024-02-07 09:05:00', '2025-10-22 21:26:15');
INSERT INTO `camera_info` VALUES (31, '化粪池区域摄像头', 2, '化粪池检修口旁', 'rtsp://192.168.1.132:554/stream', 2, 1, NULL, NULL, '2024-02-08 15:50:00', '2025-10-22 21:26:15');
INSERT INTO `camera_info` VALUES (32, '仓库门口摄像头', 3, '物业仓库入口', 'rtsp://192.168.1.133:554/stream', 1, 1, NULL, NULL, '2024-02-09 12:15:00', '2025-10-22 21:26:15');
INSERT INTO `camera_info` VALUES (33, '充电桩区域摄像头', 1, '电动汽车充电桩旁', 'rtsp://192.168.1.134:554/stream', 4, 1, NULL, NULL, '2024-02-10 14:40:00', '2025-10-22 21:26:15');

-- ----------------------------
-- Table structure for park_area
-- ----------------------------
DROP TABLE IF EXISTS `park_area`;
CREATE TABLE `park_area`  (
  `park_area_id` int(11) NOT NULL AUTO_INCREMENT,
  `park_area` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `remark` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `create_time` datetime NULL DEFAULT NULL,
  `update_time` datetime NULL DEFAULT NULL,
  PRIMARY KEY (`park_area_id`) USING BTREE,
  UNIQUE INDEX `park_area`(`park_area` ASC) USING BTREE,
  INDEX `ix_park_area_park_area_id`(`park_area_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 5 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of park_area
-- ----------------------------
INSERT INTO `park_area` VALUES (1, 'A区的新名字', 'A区的新名字的备注', '2024-01-10 00:00:00', '2025-10-26 12:28:21');
INSERT INTO `park_area` VALUES (2, 'B区的新名字', NULL, '2024-01-10 00:00:00', '2025-10-01 15:32:25');
INSERT INTO `park_area` VALUES (3, 'C区', 'C区的备注', '2024-01-10 00:00:00', '2025-10-26 12:28:39');

-- ----------------------------
-- Table structure for user
-- ----------------------------
DROP TABLE IF EXISTS `user`;
CREATE TABLE `user`  (
  `user_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_name` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `name` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `password` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `user_role` int(11) NULL DEFAULT NULL,
  `create_time` datetime NULL DEFAULT NULL,
  `update_time` datetime NULL DEFAULT NULL,
  `gender` tinyint(4) NULL DEFAULT 1,
  `phone` varchar(11) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  PRIMARY KEY (`user_id`) USING BTREE,
  UNIQUE INDEX `user_name`(`user_name` ASC) USING BTREE,
  UNIQUE INDEX `user_unique`(`phone` ASC) USING BTREE,
  INDEX `ix_user_user_id`(`user_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 28 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of user
-- ----------------------------
INSERT INTO `user` VALUES (1, '王建国（大）', '王建国', '$2b$12$8vxTelOU184OMatvlbPu1.pq.CjZ01Xr0/j.giDs91B98CgVJU9b2', 0, '2024-01-01 00:00:00', '2025-09-26 16:25:38', 1, '12345678901');
INSERT INTO `user` VALUES (2, 'admin2', '陈曦', 'encrypted_admin1243', 0, '2024-01-01 00:00:00', '2024-01-01 00:00:00', 1, '12345678902');
INSERT INTO `user` VALUES (3, 'security_manager1', '李婷', 'encrypted_security456', 1, '2024-01-02 00:00:00', '2024-01-02 00:00:00', 1, '12345678903');
INSERT INTO `user` VALUES (4, 'security_manager2', '赵亮', 'encrypted_security457', 1, '2024-01-03 00:00:00', '2024-01-03 00:00:00', 1, '12345678904');
INSERT INTO `user` VALUES (5, 'operator_1', '张伟', 'encrypted_op789', 2, '2024-01-03 00:00:00', '2024-01-03 00:00:00', 1, '12345678905');
INSERT INTO `user` VALUES (6, 'operator_2', '刘芳', 'encrypted_op012', 2, '2024-01-04 00:00:00', '2024-01-04 00:00:00', 1, '12345678906');
INSERT INTO `user` VALUES (7, 'operator_3', '黄伟', 'encrypted_op013', 2, '2024-01-04 00:00:00', '2024-01-04 00:00:00', 1, '12345678907');
INSERT INTO `user` VALUES (8, 'operator_4', '周敏', 'encrypted_op012', 2, '2024-01-04 00:00:00', '2024-01-04 00:00:00', 1, '12345678908');
INSERT INTO `user` VALUES (10, 'admin', '待定', '$2b$12$0wPNq96AExS6QbYivAtmW.bTURFzQY2JVmVL.Skc.qwaUdm.pW0Sa', 0, '2025-09-25 16:53:28', '2025-09-25 16:53:28', 1, '15083440074');
INSERT INTO `user` VALUES (25, 'string', '待定', '$2b$12$.WMfx.9PoI05UicQpD7LluiaSEx9/EI2rC6rr7IfT5VfDpA9HlZ5S', 0, '2025-09-25 17:23:37', '2025-09-25 17:23:37', 1, '15083440073');
INSERT INTO `user` VALUES (26, 'admin001', 'admin123', '$2b$12$SsHtK1ACkzRPgMeFLdstqeOE6dbFIoLg5bsU7O9YQ1t4n7R3oJEG.', 3, '2026-04-04 18:55:35', '2026-04-04 18:55:35', 1, '18859722622');

SET FOREIGN_KEY_CHECKS = 1;
