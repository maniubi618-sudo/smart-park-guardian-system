<template>
  <MainLayout>
    <div class="cameras">
      <!-- 搜索和筛选 -->
      <el-card class="search-card">
        <el-form :model="searchForm" inline>
          <el-form-item label="园区区域">
            <el-select v-model="searchForm.park_area_id" placeholder="请选择园区区域">
              <el-option v-for="area in areas" :key="area.park_area_id" :label="area.park_area_name" :value="area.park_area_id" />
            </el-select>
          </el-form-item>
          <el-form-item label="分析模式">
                <el-select v-model="searchForm.analysis_mode" placeholder="请选择分析模式">
                  <el-option label="无" value="0" />
                  <el-option label="全部" value="1" />
                  <el-option label="火警" value="4" />
                  <el-option label="柑橘成熟度" value="7" />
                </el-select>
              </el-form-item>
          <el-form-item label="摄像头状态">
            <el-select v-model="searchForm.camera_status" placeholder="请选择摄像头状态">
              <el-option label="离线" value="0" />
              <el-option label="在线(未开启安防检测)" value="1" />
              <el-option label="在线(安防检测中)" value="2" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">搜索</el-button>
            <el-button @click="resetForm">重置</el-button>
            <el-button type="success" @click="addCamera">添加摄像头</el-button>
            <el-button type="info" :icon="Picture" @click="imageAnalysis">
              图片分析
            </el-button>
            <el-button type="primary" :icon="VideoCamera" @click="localVideoAnalysis">
              本地视频分析
            </el-button>
            <el-button type="warning" :icon="VideoCamera" @click="openPhoneCamera">
              手机摄像头
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 摄像头状态统计 -->
      <el-card class="status-card" style="margin-bottom: 20px;">
        <div class="status-stats">
          <div class="stat-item">
            <div class="stat-label">摄像头总数</div>
            <div class="stat-value">{{ totalCameras }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">在线摄像头</div>
            <div class="stat-value online">{{ onlineCameras }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">离线摄像头</div>
            <div class="stat-value offline">{{ offlineCameras }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">在线率</div>
            <div class="stat-value">{{ onlineRate }}%</div>
          </div>
        </div>
      </el-card>

      <!-- 摄像头列表 -->
      <el-card class="table-card">
        <div class="table-header" style="margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
          <span></span>
          <el-button type="danger" @click="batchDeleteCameras" :disabled="selectedCameras.length === 0">
            批量删除
          </el-button>
        </div>
        <el-table :data="cameras" stripe style="width: 100%" v-loading="loading" @selection-change="handleSelectionChange">
          <el-table-column type="selection" width="55" />
          <el-table-column prop="camera_id" label="摄像头ID" width="120" align="center" />
          <el-table-column prop="camera_name" label="摄像头名称" />
          <el-table-column prop="park_area" label="所属区域" width="150" />
          <el-table-column prop="rtsp_url" label="RTSP地址" />
          <el-table-column prop="analysis_mode" label="分析模式" width="120">
            <template #default="scope">
              {{ getAnalysisModeName(scope.row.analysis_mode) }}
            </template>
          </el-table-column>
          <el-table-column prop="camera_status" label="状态" width="150">
            <template #default="scope">
              <el-tag :type="getCameraStatusTag(scope.row.camera_status)">
                {{ getCameraStatusName(scope.row.camera_status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="360">
            <template #default="scope">
              <el-button type="primary" size="small" @click="editCamera(scope.row)">
                编辑
              </el-button>
              <el-button type="success" size="small" @click="testCamera(scope.row)">
                测试
              </el-button>
              <el-button type="warning" size="small" @click="previewCamera(scope.row)">
                预览
              </el-button>
              <el-button type="info" size="small" @click="analysisTestCamera(scope.row)">
                分析测试
              </el-button>
              <el-button type="danger" size="small" @click="deleteCamera(scope.row)">
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页 -->
        <div class="pagination" v-if="total > 0">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            :total="total"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </el-card>

      <!-- 摄像头预览对话框 -->
      <el-dialog
        v-model="previewDialogVisible"
        title="摄像头预览"
        width="700px"
        :close-on-click-modal="false"
        @close="handlePreviewDialogClose"
      >
        <div class="preview-container">
          <div v-if="previewLoading" class="preview-loading">
            <el-icon class="is-loading" :size="40"><Loading /></el-icon>
            <p>正在获取预览图像...</p>
          </div>
          <div v-else-if="previewImage" class="preview-image-wrapper">
            <img :src="previewImage" alt="摄像头预览" class="preview-image" />
            <div class="preview-info">
              <p><strong>摄像头:</strong> {{ previewCameraName }}</p>
              <p><strong>时间:</strong> {{ formatTime(previewTimestamp) }}</p>
              <p v-if="isStreaming" class="streaming-indicator">
                <el-icon color="#67C23A"><Check /></el-icon> 正在直播
              </p>
              <p v-else class="streaming-indicator">
                <el-icon color="#E6A23C"><VideoCamera /></el-icon> 已暂停
              </p>
              <p v-if="isStreaming" class="fps-indicator">
                <strong>FPS:</strong> {{ previewFps.toFixed(1) }}
              </p>
            </div>
          </div>
          <div v-else class="preview-error">
            <el-icon :size="40" color="#F56C6C"><CircleClose /></el-icon>
            <p>{{ previewError || '无法获取预览图像' }}</p>
          </div>
        </div>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="previewDialogVisible = false">关闭</el-button>
            <el-button v-if="!isStreaming" type="primary" @click="startStream" :loading="previewLoading">
              开始直播
            </el-button>
            <el-button v-else type="warning" @click="stopStream">
              停止直播
            </el-button>
          </span>
        </template>
      </el-dialog>

      <!-- 摄像头分析测试对话框 -->
      <el-dialog
        v-model="analysisDialogVisible"
        title="摄像头分析测试"
        width="800px"
        :close-on-click-modal="false"
        @close="handleAnalysisDialogClose"
      >
        <div class="analysis-container">
          <div v-if="analysisLoading" class="preview-loading">
            <el-icon class="is-loading" :size="40"><Loading /></el-icon>
            <p>正在启动分析测试...</p>
          </div>
          <div v-else-if="analysisImage" class="preview-image-wrapper">
            <img :src="analysisImage" alt="分析测试" class="preview-image" />
            <div class="preview-info">
              <p><strong>摄像头:</strong> {{ analysisCameraName }}</p>
              <p><strong>时间:</strong> {{ formatTime(analysisTimestamp) }}</p>
              <p v-if="isAnalysisStreaming" class="streaming-indicator">
                <el-icon color="#67C23A"><Check /></el-icon> 正在分析
              </p>
              <p v-else class="streaming-indicator">
                <el-icon color="#E6A23C"><VideoCamera /></el-icon> 已暂停
              </p>
              <p v-if="isAnalysisStreaming" class="fps-indicator">
                <strong>FPS:</strong> {{ analysisFps.toFixed(1) }}
              </p>
              <div class="write-to-db-option" style="margin-top: 15px; display: flex; align-items: center; justify-content: space-between;">
                <span style="font-size: 14px; color: #606266;">将警告信息写入数据库</span>
                <el-switch v-model="writeToDatabase" active-text="是" inactive-text="否" />
              </div>
              <div class="write-to-db-option" style="margin-top: 10px; display: flex; align-items: center; justify-content: space-between;">
                <span style="font-size: 14px; color: #606266;">警告提示音</span>
                <el-switch v-model="enableWarningSound" active-text="是" inactive-text="否" />
              </div>
              <div v-if="analysisResults" class="analysis-results">
                <h4>分析结果:</h4>
                <div class="analysis-grid">
                  <div 
                    v-for="(result, index) in filteredAnalysisResults" 
                    :key="index"
                    class="analysis-item"
                    :class="{ 'warning': result.value.includes('检测到') || (result.value.includes('人') && parseInt(result.value) > 0) || (result.value.includes('辆') && parseInt(result.value) > 0) }"
                  >
                    <div class="analysis-label">{{ result.label }}</div>
                    <div class="analysis-value">{{ result.value }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="preview-error">
            <el-icon :size="40" color="#F56C6C"><CircleClose /></el-icon>
            <p>{{ analysisError || '无法启动分析测试' }}</p>
          </div>
        </div>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="handleAnalysisDialogClose">关闭</el-button>
            <el-button v-if="!isAnalysisStreaming" type="primary" @click="startAnalysisTest" :loading="analysisLoading">
              开始分析
            </el-button>
            <el-button v-else type="warning" @click="stopAnalysisTest">
              停止分析
            </el-button>
          </span>
        </template>
      </el-dialog>

      <!-- 本地视频分析对话框 -->
      <el-dialog
        v-model="localVideoDialogVisible"
        title="本地视频分析"
        width="900px"
        :close-on-click-modal="false"
      >
        <div class="local-video-analysis">
          <!-- 视频选择区域 -->
          <div v-if="!isLocalAnalysisStarted" class="video-upload-section">
            <!-- 上传区域 -->
            <div v-if="!selectedVideoFile" class="upload-area">
              <el-upload
                class="upload-demo"
                drag
                action=""
                :auto-upload="false"
                :on-change="handleVideoUpload"
                :limit="1"
                accept=".mp4,.avi,.mov,.wmv"
              >
                <el-icon class="el-icon--upload"><Upload /></el-icon>
                <div class="el-upload__text">将视频文件拖到此处，或 <em>点击上传</em></div>
                <template #tip>
                  <div class="el-upload__tip">
                    请上传 MP4、AVI、MOV、WMV 格式的视频文件
                  </div>
                </template>
              </el-upload>
            </div>
            <!-- 视频预览区域 -->
            <div v-else class="video-preview-area">
              <div class="video-preview">
                <video :src="videoUrl" controls style="width: 100%; max-height: 300px;"></video>
              </div>
              <div class="selected-file" style="margin-top: 10px;">
                <el-tag>{{ selectedVideoFile.name }}</el-tag>
                <el-button type="danger" size="small" @click="selectedVideoFile = null; videoUrl = ''">
                  移除
                </el-button>
              </div>
            </div>
            <el-form :model="localAnalysisForm" style="margin-top: 20px;">
              <el-form-item label="分析模式">
                <el-select v-model="localAnalysisForm.analysisMode" placeholder="请选择分析模式">
                  <el-option label="全部" value="1" />
                  <el-option label="火警" value="4" />
                  <el-option label="柑橘成熟度" value="7" />
                  <el-option label="作物病害检测" value="8" />
                </el-select>
              </el-form-item>
              <!-- 作物类型选择，仅在作物病害检测模式下显示 -->
              <el-form-item v-if="localAnalysisForm.analysisMode === '8'" label="作物类型">
                <el-select v-model="localAnalysisForm.cropType" placeholder="请选择作物类型">
                  <el-option v-for="crop in availableCrops" :key="crop" :label="getCropLabel(crop)" :value="crop" />
                </el-select>
              </el-form-item>
              <el-form-item label="分析间隔（帧）">
                <el-input-number v-model="localAnalysisForm.frameInterval" :min="1" :max="30" :step="1" />
              </el-form-item>
            </el-form>
          </div>
          
          <!-- 分析过程区域 -->
          <div v-else class="analysis-process-section">
            <div class="video-player">
              <video ref="videoPlayer" :src="videoUrl" controls style="width: 100%; max-height: 400px;"></video>
            </div>
            
            <!-- 分析进度条 -->
            <div class="progress-section">
              <el-progress
                :percentage="analysisProgress"
                :format="formatProgress"
                :color="progressColor"
              />
              <div class="progress-info">
                <span>已分析: {{ processedFrames }} / {{ totalFrames }} 帧</span>
                <span>预计剩余: {{ remainingTime }}秒</span>
              </div>
            </div>
            
            <!-- 分析结果 -->
            <div class="analysis-results" v-if="filteredLocalAnalysisResults.length > 0">
              <h3>当前帧分析结果</h3>
              <div class="analysis-grid">
                <div 
                  v-for="(result, index) in filteredLocalAnalysisResults" 
                  :key="index"
                  class="analysis-item"
                  :class="{ 'warning': result.value.includes('检测到') || (result.value.includes('人') && parseInt(result.value) > 0) || (result.value.includes('辆') && parseInt(result.value) > 0) || result.label.includes('🌱') }"
                >
                  <div class="analysis-label">{{ result.label }}</div>
                  <div class="analysis-value">{{ result.value }}</div>
                </div>
              </div>
            </div>
            
            <!-- 总分析结果 -->
            <div class="total-analysis-results" v-if="!isLocalAnalysisStarted && totalFrames.value > 0">
              <h3>总分析结果</h3>
              <el-descriptions :column="2">
                <el-descriptions-item label="人员检测">
                  {{ totalAnalysisResults.person }} 人
                </el-descriptions-item>
                <el-descriptions-item label="火焰检测">
                  {{ totalAnalysisResults.fire }} 次
                </el-descriptions-item>
                <el-descriptions-item label="烟雾检测">
                  {{ totalAnalysisResults.smoke }} 次
                </el-descriptions-item>
                <el-descriptions-item label="分析帧数">
                  {{ processedFrames.value }} / {{ totalFrames.value }} 帧
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </div>
        </div>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="handleLocalVideoDialogClose">关闭</el-button>
            <el-button 
              v-if="!isLocalAnalysisStarted && selectedVideoFile" 
              type="primary" 
              @click="startLocalVideoAnalysis"
              :loading="localAnalysisLoading"
            >
              开始分析
            </el-button>
            <el-button 
              v-else-if="isLocalAnalysisStarted" 
              type="warning" 
              @click="stopLocalVideoAnalysis"
            >
              停止分析
            </el-button>
          </span>
        </template>
      </el-dialog>

      <!-- 手机摄像头对话框 -->
      <el-dialog
        v-model="phoneCameraDialogVisible"
        title="手机摄像头"
        width="900px"
        class="phone-camera-dialog"
        :close-on-click-modal="false"
        @close="handlePhoneCameraDialogClose"
      >
        <el-tabs v-model="phoneCameraMode" type="border-card">
          <el-tab-pane label="手机推流观看" name="phone-viewer">
            <div class="phone-camera-phone-viewer-mode">
              <div class="video-container-wrapper">
                <div class="video-container" :class="{ 'mirror': phoneViewerMirror }">
                  <canvas ref="phoneViewerCanvas" class="phone-viewer-canvas"></canvas>
                </div>
                <div v-if="!phoneViewerConnected" class="phone-camera-placeholder">
                  <el-icon :size="60" color="#909399"><VideoCamera /></el-icon>
                  <p>等待手机连接...</p>
                  <p style="font-size: 12px; color: #909399;">请先切换到"手机连接"标签页</p>
                </div>
              </div>
              <div class="phone-camera-controls">
                <el-button type="primary" @click="startPhoneViewer" :disabled="phoneViewerConnected">
                  连接观看
                </el-button>
                <el-button type="danger" @click="stopPhoneViewer" :disabled="!phoneViewerConnected">
                  断开连接
                </el-button>
                <el-button @click="togglePhoneViewerMirror" :disabled="!phoneViewerConnected">
                  {{ phoneViewerMirror ? '取消镜像' : '水平镜像' }}
                </el-button>
              </div>
              <div v-if="phoneViewerConnected" class="phone-camera-info">
                <el-descriptions :column="3" border size="small">
                  <el-descriptions-item label="分辨率">{{ phoneViewerResolution }}</el-descriptions-item>
                  <el-descriptions-item label="帧率">{{ phoneViewerFps }} fps</el-descriptions-item>
                  <el-descriptions-item label="延迟">{{ phoneViewerLatency }} ms</el-descriptions-item>
                </el-descriptions>
              </div>
              
              <!-- 分析控制 -->
              <div class="phone-camera-analysis-section" style="margin-top: 20px;">
                <el-divider content-position="left">分析控制</el-divider>
                <div style="margin-bottom: 15px;">
                  <el-select v-model="phoneCameraAnalysisMode" placeholder="请选择分析模式" style="width: 200px; margin-right: 10px;">
                    <el-option label="全部" value="1" />
                    <el-option label="火警" value="4" />
                    <el-option label="柑橘成熟度" value="7" />
                    <el-option label="作物病害检测" value="8" />
                  </el-select>
                  <!-- 作物类型选择，仅在作物病害检测模式下显示 -->
                  <el-select 
                    v-if="phoneCameraAnalysisMode === '8'"
                    v-model="phoneCameraCropType" 
                    placeholder="请选择作物类型" 
                    style="width: 150px; margin-right: 10px;"
                  >
                    <el-option v-for="crop in availableCrops" :key="crop" :label="getCropLabel(crop)" :value="crop" />
                  </el-select>
                  <el-button type="success" @click="startPhoneCameraAnalysis" :disabled="!phoneViewerConnected || isPhoneCameraAnalyzing">
                    开始分析
                  </el-button>
                  <el-button type="warning" @click="stopPhoneCameraAnalysis" :disabled="!isPhoneCameraAnalyzing">
                    停止分析
                  </el-button>
                </div>
                
                <!-- 分析结果 -->
                <div v-if="phoneCameraAnalysisResults" class="analysis-results">
                  <h4>分析结果:</h4>
                  <div class="analysis-grid">
                    <div 
                      v-for="(result, index) in filteredPhoneCameraAnalysisResults" 
                      :key="index"
                      class="analysis-item"
                      :class="{ 'warning': result.value.includes('检测到') || (result.value.includes('人') && parseInt(result.value) > 0) || (result.value.includes('辆') && parseInt(result.value) > 0) }"
                    >
                      <div class="analysis-label">{{ result.label }}</div>
                      <div class="analysis-value">{{ result.value }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>
          <el-tab-pane label="手机连接" name="phone">
            <div class="phone-camera-phone-mode">
              <el-alert type="info" :closable="false" style="margin-bottom: 20px;">
                <template #title>
                  请确保您的手机和电脑在同一局域网内
                </template>
              </el-alert>
              
              <div class="connection-info">
                <div class="info-item">
                  <span class="info-label">本机IP地址:</span>
                  <el-tag type="success" size="large">{{ localIPAddress }}</el-tag>
                  <el-button size="small" @click="copyLocalIP">复制</el-button>
                </div>
                <div class="info-item">
                  <span class="info-label">手机连接地址:</span>
                  <el-input :value="phonePushUrl" readonly style="width: 400px; margin-right: 10px;" />
                  <el-button size="small" @click="copyPhonePushUrl">复制</el-button>
                </div>
              </div>

              <div class="qr-code-section" v-if="phonePushQrCodeUrl">
                <h4>扫描二维码连接:</h4>
                <div class="qr-code-wrapper">
                  <img :src="phonePushQrCodeUrl" alt="QR Code" class="qr-code" />
                </div>
                <p style="color: #909399; font-size: 12px; margin-top: 10px;">使用手机浏览器扫描二维码访问</p>
              </div>

              <div class="instructions">
                <h4>连接步骤:</h4>
                <ol>
                  <li>确保手机和电脑连接到同一Wi-Fi网络</li>
                  <li>在手机浏览器中输入上方连接地址，或扫描二维码</li>
                  <li>允许浏览器访问摄像头权限</li>
                  <li>切换到"手机推流观看"标签页查看画面</li>
                  <li>在手机端可点击闪光灯按钮开启/关闭闪光灯</li>
                </ol>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="handlePhoneCameraDialogClose">关闭</el-button>
          </span>
        </template>
      </el-dialog>

      <!-- 图片分析对话框 -->
      <el-dialog
        v-model="imageAnalysisDialogVisible"
        title="图片分析"
        width="900px"
        :close-on-click-modal="false"
        @close="handleImageAnalysisDialogClose"
      >
        <div class="image-analysis">
          <!-- 图片上传区域 -->
          <div v-if="!imageAnalysisResult" class="image-upload-section">
            <div v-if="!selectedImageFile" class="upload-area">
              <el-upload
                class="upload-demo"
                drag
                action=""
                :auto-upload="false"
                :on-change="handleImageUpload"
                :limit="1"
                accept=".jpg,.jpeg,.png,.bmp"
              >
                <el-icon class="el-icon--upload"><Upload /></el-icon>
                <div class="el-upload__text">将图片文件拖到此处，或 <em>点击上传</em></div>
                <template #tip>
                  <div class="el-upload__tip">
                    请上传 JPG、PNG、BMP 格式的图片文件
                  </div>
                </template>
              </el-upload>
            </div>
            <!-- 图片预览区域 -->
            <div v-else class="image-preview-area">
              <div class="image-preview">
                <img :src="imageUrl" alt="预览图片" style="width: 100%; max-height: 400px; object-fit: contain;" />
              </div>
              <div class="selected-file" style="margin-top: 10px;">
                <el-tag>{{ selectedImageFile.name }}</el-tag>
                <el-button type="danger" size="small" @click="clearSelectedImage">
                  移除
                </el-button>
              </div>
            </div>
            <el-form :model="imageAnalysisForm" style="margin-top: 20px;">
              <el-form-item label="分析模式">
                <el-select v-model="imageAnalysisForm.analysisMode" placeholder="请选择分析模式">
                  <el-option label="作物病害检测" value="cropDisease" />
                  <el-option label="柑橘成熟度" value="citrus" />
                </el-select>
              </el-form-item>
              <el-form-item v-if="imageAnalysisForm.analysisMode === 'cropDisease'" label="作物类型">
                <el-select v-model="imageAnalysisForm.cropType" placeholder="请选择作物类型">
                  <el-option v-for="crop in availableCrops" :key="crop" :label="getCropLabel(crop)" :value="crop" />
                </el-select>
              </el-form-item>
            </el-form>
          </div>
          
          <!-- 分析结果区域 -->
          <div v-else class="analysis-result-section">
            <div class="result-image">
              <img :src="imageAnalysisResult.annotated_image" alt="分析结果" style="width: 100%; max-height: 500px; object-fit: contain;" />
            </div>
            <div class="result-info" style="margin-top: 20px;">
              <el-alert
                :title="imageAnalysisResult.message"
                type="success"
                :closable="false"
                style="margin-bottom: 20px;"
              />
              <div v-if="imageAnalysisForm.analysisMode === 'cropDisease' && imageAnalysisResult.crop_type" style="margin-bottom: 15px;">
                <el-tag type="info">作物类型: {{ getCropLabel(imageAnalysisResult.crop_type) }}</el-tag>
              </div>
              <div v-if="imageAnalysisResult.predictions && imageAnalysisResult.predictions.length > 0" class="predictions-list">
                <h4 style="margin-bottom: 15px;">检测结果:</h4>
                <el-table :data="imageAnalysisResult.predictions" style="width: 100%">
                  <el-table-column prop="class_name" label="病害类别" width="200" />
                  <el-table-column prop="confidence" label="置信度" width="120">
                    <template #default="scope">
                      {{ (scope.row.confidence * 100).toFixed(1) }}%
                    </template>
                  </el-table-column>
                  <el-table-column v-if="imageAnalysisForm.analysisMode === 'citrus'" prop="maturity_label" label="成熟度" width="120" />
                  <el-table-column v-if="imageAnalysisForm.analysisMode === 'citrus'" prop="days_to_ripe" label="预计成熟天数" width="140" />
                </el-table>
              </div>
            </div>
          </div>
        </div>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="handleImageAnalysisDialogClose">关闭</el-button>
            <el-button
              v-if="!imageAnalysisResult && selectedImageFile"
              type="primary"
              @click="startImageAnalysis"
              :loading="imageAnalysisLoading"
            >
              开始分析
            </el-button>
            <el-button v-if="imageAnalysisResult" type="info" @click="resetImageAnalysis">
              重新分析
            </el-button>
          </span>
        </template>
      </el-dialog>

      <!-- 摄像头编辑对话框 -->
      <el-dialog
        v-model="dialogVisible"
        :title="isEdit ? '编辑摄像头' : '添加摄像头'"
        width="600px"
      >
        <el-form :model="cameraForm" :rules="cameraRules" ref="cameraFormRef">
          <el-form-item label="摄像头名称" prop="camera_name">
            <el-input v-model="cameraForm.camera_name" placeholder="请输入摄像头名称" />
          </el-form-item>
          <el-form-item label="所属区域" prop="park_area_id">
            <el-select v-model="cameraForm.park_area_id" placeholder="请选择所属区域">
              <el-option v-for="area in areas" :key="area.park_area_id" :label="area.park_area" :value="area.park_area_id" />
            </el-select>
          </el-form-item>
          <el-form-item label="RTSP地址" prop="rtsp_url">
            <el-input v-model="cameraForm.rtsp_url" placeholder="请输入RTSP地址" />
          </el-form-item>
          <el-form-item label="安装位置" prop="install_position">
            <el-input v-model="cameraForm.install_position" placeholder="请输入安装位置" />
          </el-form-item>
          <el-form-item label="分析模式" prop="analysis_mode">
                <el-select v-model="cameraForm.analysis_mode" placeholder="请选择分析模式">
                  <el-option label="无" :value="0" />
                  <el-option label="全部" :value="1" />
                  <el-option label="火警" :value="4" />
                  <el-option label="柑橘成熟度" :value="7" />
                </el-select>
              </el-form-item>
          <el-form-item label="摄像头IP" prop="camera_ip">
            <el-input v-model="cameraForm.camera_ip" placeholder="请输入摄像头IP" />
          </el-form-item>
          <el-form-item label="备注" prop="remark">
            <el-input v-model="cameraForm.remark" type="textarea" :rows="3" placeholder="请输入备注" />
          </el-form-item>
        </el-form>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="dialogVisible = false">取消</el-button>
            <el-button type="primary" @click="submitCamera" :loading="submitLoading">提交</el-button>
          </span>
        </template>
      </el-dialog>

      
    </div>
  </MainLayout>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, reactive } from 'vue'
import { useCameraStore } from '../../stores/cameras'
import { useAreaStore } from '../../stores/areas'
import MainLayout from '../../components/MainLayout.vue'
import { VideoCamera, Loading, CircleClose, Check, Upload, Picture } from '@element-plus/icons-vue'
import { citrusApi, cropDiseaseApi } from '../../services/api.js'
import { ElMessageBox, ElMessage } from 'element-plus'
import QRCode from 'qrcode'

const cameraStore = useCameraStore()
const areaStore = useAreaStore()

// 过滤掉已关闭的检测结果
const filteredAnalysisResults = computed(() => {
  if (!analysisResults.value) return []
  return analysisResults.value.filter(result => {
    // 隐藏的检测类型（保留人员检测）
    const hiddenLabels = ['未戴安全帽', '未穿反光衣', '车辆检测', '区域入侵']
    return !hiddenLabels.includes(result.label)
  })
})

// 过滤手机摄像头分析结果
const filteredPhoneCameraAnalysisResults = computed(() => {
  if (!phoneCameraAnalysisResults.value) return []
  return phoneCameraAnalysisResults.value.filter(result => {
    // 隐藏的检测类型（保留人员检测）
    const hiddenLabels = ['未戴安全帽', '未穿反光衣', '车辆检测', '区域入侵']
    return !hiddenLabels.includes(result.label)
  })
})

// 过滤本地视频分析结果
const filteredLocalAnalysisResults = computed(() => {
  if (!localAnalysisResults.value) return []
  return localAnalysisResults.value.filter(result => {
    // 隐藏的检测类型（保留人员检测）
    const hiddenLabels = ['未戴安全帽', '未穿反光衣', '车辆检测', '区域入侵']
    return !hiddenLabels.includes(result.label)
  })
})

// 搜索表单
const searchForm = reactive({
  park_area_id: '',
  analysis_mode: '',
  camera_status: ''
})

// 分页
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const loading = ref(false)

// 摄像头列表
const cameras = ref([])
const selectedCameras = ref([])
const areas = ref([])

// 编辑对话框
const dialogVisible = ref(false)
const isEdit = ref(false)
const cameraForm = reactive({
  camera_info_id: '',
  camera_name: '',
  park_area_id: '',
  install_position: '',
  rtsp_url: '',
  analysis_mode: 0,
  camera_ip: '',
  remark: ''
})

const cameraFormRef = ref(null)
const submitLoading = ref(false)

// 预览相关
const previewDialogVisible = ref(false)
const currentPreviewCameraId = ref(null)
const previewCameraName = ref('')
const previewImage = ref('')
const previewTimestamp = ref('')
const previewLoading = ref(false)
const previewError = ref('')
const isStreaming = ref(false)
const wsConnection = ref(null)
// FPS相关
const previewFps = ref(0)
const previewFrameCount = ref(0)
const previewLastTime = ref(0)

// 分析测试相关
const analysisDialogVisible = ref(false)
const currentAnalysisCameraId = ref(null)
const analysisCameraName = ref('')
const analysisImage = ref('')
const analysisTimestamp = ref('')
const analysisResults = ref(null)
const analysisError = ref('')
const isAnalysisStreaming = ref(false)
const analysisLoading = ref(false)
const analysisWsConnection = ref(null)
const writeToDatabase = ref(false)
// FPS相关
const analysisFps = ref(0)
const analysisFrameCount = ref(0)
const analysisLastTime = ref(0)
// 告警状态管理
const lastAlertState = ref('') // 初始化为空字符串，与currentAlertKey类型一致
const alertDebounceTimer = ref(null)
const ALERT_DEBOUNCE_TIME = 500 // 500毫秒防抖，提高响应速度
// 告警提示音管理
const enableWarningSound = ref(true) // 默认开启提示音
const currentAudio = ref(null) // 当前播放的音频

// 停止当前播放的提示音
const stopWarningSound = () => {
  if (currentAudio.value) {
    currentAudio.value.pause()
    currentAudio.value.currentTime = 0
    currentAudio.value = null
  }
}

// 监听enableWarningSound变化，关闭时立即停止提示音
watch(enableWarningSound, (newValue) => {
  if (!newValue) {
    stopWarningSound()
  }
})

// 监听writeToDatabase变化，通过WebSocket发送消息更新值
watch(writeToDatabase, (newValue) => {
  if (isAnalysisStreaming.value && analysisWsConnection.value && analysisWsConnection.value.readyState === WebSocket.OPEN) {
    // 通过WebSocket发送消息更新write_to_database值
    analysisWsConnection.value.send(JSON.stringify({
      action: 'update_write_to_database',
      write_to_database: newValue
    }))
  }
})

// 本地视频分析相关
const localVideoDialogVisible = ref(false)
const selectedVideoFile = ref(null)
const videoUrl = ref('')
const videoPlayer = ref(null)
const localAnalysisForm = reactive({
  analysisMode: '1',
  frameInterval: 5,
  cropType: 'rice' // 作物类型选择，用于作物病害检测
})
const isLocalAnalysisStarted = ref(false)
const localAnalysisLoading = ref(false)
const analysisProgress = ref(0)
const processedFrames = ref(0)
const totalFrames = ref(0)
const remainingTime = ref(0)
const localAnalysisResults = ref([])
const analysisInterval = ref(null)
const totalAnalysisResults = ref({
  helmet: 0,
  vest: 0,
  fire: 0,
  smoke: 0,
  person: 0,
  vehicle: 0,
  intrusion: 0
})

// 手机摄像头相关状态
const phoneCameraDialogVisible = ref(false)
const phoneCameraMode = ref('phone')
const phoneCameraVideo = ref(null)
const phoneCameraStreaming = ref(false)
const phoneCameraStream = ref(null)
const phoneCameraFacing = ref('environment')
const phoneCameraMirror = ref(false)
const phoneCameraResolution = ref('')
const phoneCameraFps = ref(0)
const phoneCameraFrameCount = ref(0)
const phoneCameraLastTime = ref(0)
const phoneCameraFpsInterval = ref(null)

// IP地址和连接相关
const localIPAddress = ref('')
const phoneConnectionUrl = ref('')
const qrCodeUrl = ref('')
const phonePushUrl = ref('')
const phonePushQrCodeUrl = ref('')

// 手机推流观看相关
const phoneViewerCanvas = ref(null)
const phoneViewerConnected = ref(false)
const phoneViewerWs = ref(null)
const phoneViewerMirror = ref(false)
const phoneViewerResolution = ref('')
const phoneViewerFps = ref(0)
const phoneViewerLatency = ref(0)
const phoneViewerFrameCount = ref(0)
const phoneViewerLastTime = ref(0)
const phoneViewerFpsInterval = ref(null)
const phoneViewerRenderBusy = ref(false)
const phoneViewerQueuedFrame = ref(null)

// 手机摄像头分析相关
const phoneCameraAnalysisMode = ref('1')
const phoneCameraCropType = ref('strawberry') // 作物类型选择，用于作物病害检测
const isPhoneCameraAnalyzing = ref(false)
const phoneCameraAnalysisResults = ref(null)
const phoneCameraAnalysisInterval = ref(null)
const phoneCameraLastFrameData = ref(null)
const phoneCameraLastAlertState = ref('') // 手机摄像头分析的告警状态
const phoneCameraReportedDiseases = ref({})  // 已上报病害去重：{ diseaseName: timestamp }
const PHONE_CAMERA_ALARM_COOLDOWN_MS = 30000  // 同一病害 30 秒内不重复写库

// 手机摄像头位置相关
const phoneCameraLocation = ref(null) // { latitude, longitude }

// 图片分析相关
const imageAnalysisDialogVisible = ref(false)
const selectedImageFile = ref(null)
const imageUrl = ref('')
const availableCrops = ref([])
const imageAnalysisForm = reactive({
  analysisMode: 'cropDisease',
  cropType: 'rice'
})
const imageAnalysisResult = ref(null)
const imageAnalysisLoading = ref(false)

// 进度条颜色
const progressColor = computed(() => {
  if (analysisProgress.value < 30) return '#536f88'
  if (analysisProgress.value < 70) return '#c58a45'
  return '#f56c6c'
})

const cameraRules = {
  camera_name: [
    { required: true, message: '请输入摄像头名称', trigger: 'blur' }
  ],
  park_area_id: [
    { required: true, message: '请选择所属区域', trigger: 'blur' }
  ],
  rtsp_url: [
    { required: true, message: '请输入RTSP地址', trigger: 'blur' }
  ]
}

// 状态统计
const totalCameras = computed(() => cameraStore.totalCameras)
const onlineCameras = computed(() => cameraStore.onlineCameras)
const offlineCameras = computed(() => cameraStore.offlineCameras)
const onlineRate = computed(() => {
  if (totalCameras.value === 0) return 0
  return Math.round((onlineCameras.value / totalCameras.value) * 100)
})

// 方法
const getAnalysisModeName = (mode) => {
  const modeMap = {
    0: '无',
    1: '全部',
    2: '安全规范',
    3: '区域入侵',
    4: '火警',
    5: '害虫检测',
    6: '作物长势异常',
    7: '柑橘成熟度'
  }
  return modeMap[mode] || '未知'
}

const getCameraStatusName = (status) => {
  const statusMap = {
    0: '离线',
    1: '在线(未开启安防检测)',
    2: '在线(安防检测中)'
  }
  return statusMap[status] || '未知'
}

const getCameraStatusTag = (status) => {
  const tagMap = {
    0: 'danger',
    1: 'warning',
    2: 'success'
  }
  return tagMap[status] || 'info'
}

const handleSearch = async () => {
  currentPage.value = 1
  await fetchCameras()
}

const resetForm = () => {
  searchForm.park_area_id = ''
  searchForm.analysis_mode = ''
  searchForm.camera_status = ''
  currentPage.value = 1
  fetchCameras()
}

const fetchCameras = async () => {
  loading.value = true
  try {
    // 构建参数，过滤掉空值
    const params = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value
    }
    
    // 只添加非空值，并将字符串转换为整数
    if (searchForm.park_area_id !== '') params.park_area_id = parseInt(searchForm.park_area_id)
    if (searchForm.analysis_mode !== '') params.analysis_mode = parseInt(searchForm.analysis_mode)
    if (searchForm.camera_status !== '') params.camera_status = parseInt(searchForm.camera_status)
    
    const result = await cameraStore.fetchCameras(params)
    if (result.success) {
      cameras.value = result.data.rows || []
      total.value = result.data.total || 0
    } else {
      console.error('获取摄像头列表失败:', result.message)
      ElMessage.error('获取摄像头列表失败: ' + result.message)
    }
  } catch (error) {
    console.error('获取摄像头列表失败:', error)
    ElMessage.error('获取摄像头列表失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

const fetchAreas = async () => {
  try {
    const result = await areaStore.fetchAreas()
    if (result.success) {
      areas.value = result.data.rows || []
    }
  } catch (error) {
    console.error('获取园区区域失败:', error)
  }
}

const handleSizeChange = (size) => {
  pageSize.value = size
  fetchCameras()
}

const handleCurrentChange = (current) => {
  currentPage.value = current
  fetchCameras()
}

const addCamera = () => {
  isEdit.value = false
  // 重置表单
  cameraForm.camera_info_id = ''
  cameraForm.camera_name = ''
  cameraForm.park_area_id = ''
  cameraForm.install_position = ''
  cameraForm.rtsp_url = ''
  cameraForm.analysis_mode = 0
  cameraForm.camera_ip = ''
  cameraForm.remark = ''
  // 重置表单验证状态
  if (cameraFormRef.value) {
    cameraFormRef.value.resetFields()
  }
  dialogVisible.value = true
}

const editCamera = (camera) => {
  isEdit.value = true
  cameraForm.camera_info_id = camera.camera_id
  cameraForm.camera_name = camera.camera_name
  cameraForm.park_area_id = camera.park_area_id
  cameraForm.install_position = camera.install_position || ''
  cameraForm.rtsp_url = camera.rtsp_url
  cameraForm.analysis_mode = Number(camera.analysis_mode)
  cameraForm.camera_ip = camera.camera_ip
  cameraForm.remark = camera.remark
  dialogVisible.value = true
}

const deleteCamera = async (camera) => {
  // 确认删除
  try {
    await ElMessageBox.confirm('确定要删除这个摄像头吗？', '删除确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    // 调用删除API
    const result = await cameraStore.deleteCamera(camera.camera_id)
    if (result.success) {
      // 删除成功，刷新列表和状态统计
      await fetchCameras()
      await cameraStore.fetchStatusReport()
      ElMessage.success('删除成功')
    } else {
      ElMessage.error(result.message)
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除摄像头失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 处理表格选择变化
const handleSelectionChange = (val) => {
  selectedCameras.value = val
}

// 批量删除摄像头
const batchDeleteCameras = async () => {
  if (selectedCameras.value.length === 0) return
  
  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${selectedCameras.value.length} 个摄像头吗？`, '删除确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const ids = selectedCameras.value.map(camera => camera.camera_id).join(',')
    const result = await cameraStore.deleteCamera(ids)
    if (result.success) {
      selectedCameras.value = []
      // 删除成功，刷新列表和状态统计
      await fetchCameras()
      await cameraStore.fetchStatusReport()
      ElMessage.success('删除成功')
    } else {
      ElMessage.error(result.message)
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除摄像头失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 测试摄像头连接状态
const testCamera = async (camera) => {
  try {
    const result = await cameraStore.testCamera(camera.camera_id)
    if (result.success) {
      ElMessage.success('连接成功')
    } else {
      ElMessage.error('连接失败: ' + result.message)
    }
  } catch (error) {
    console.error('测试摄像头连接失败:', error)
    ElMessage.error('测试失败')
  }
}

// 预览摄像头
const previewCamera = async (camera) => {
  currentPreviewCameraId.value = camera.camera_id
  previewCameraName.value = camera.camera_name
  previewDialogVisible.value = true
  await loadPreviewImage()
}

// 加载预览图像
const loadPreviewImage = async () => {
  if (!currentPreviewCameraId.value) return

  previewLoading.value = true
  previewImage.value = ''
  previewError.value = ''

  try {
    const result = await cameraStore.getCameraPreview(currentPreviewCameraId.value)
    if (result.success) {
      previewImage.value = result.data.image
      previewTimestamp.value = result.data.timestamp
    } else {
      previewError.value = result.message || '获取预览图像失败'
    }
  } catch (error) {
    console.error('获取预览图像失败:', error)
    previewError.value = '获取预览图像失败'
  } finally {
    previewLoading.value = false
  }
}

// 格式化时间
const formatTime = (isoTime) => {
  if (!isoTime) return ''
  const date = new Date(isoTime)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

// 刷新预览
const refreshPreview = () => {
  loadPreviewImage()
}

// 开始直播
const startStream = async () => {
  if (!currentPreviewCameraId.value) return

  previewLoading.value = true
  previewError.value = ''

  try {
    // 关闭之前的连接
    stopStream()

    // 建立WebSocket连接
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/api/v1/camera_infos/preview/${currentPreviewCameraId.value}/ws`
    wsConnection.value = new WebSocket(wsUrl)

    wsConnection.value.onopen = () => {
      console.log('WebSocket连接已建立')
      isStreaming.value = true
      previewLoading.value = false
    }

    wsConnection.value.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.error) {
          previewError.value = data.error
          isStreaming.value = false
        } else if (data.image) {
          previewImage.value = data.image
          previewTimestamp.value = data.timestamp
          
          // 计算FPS
          const now = Date.now()
          previewFrameCount.value++
          if (now - previewLastTime.value >= 1000) {
            previewFps.value = previewFrameCount.value * 1000 / (now - previewLastTime.value)
            previewFrameCount.value = 0
            previewLastTime.value = now
          }
        }
      } catch (error) {
        console.error('解析WebSocket消息失败:', error)
      }
    }

    wsConnection.value.onclose = () => {
      console.log('WebSocket连接已关闭')
      isStreaming.value = false
    }

    wsConnection.value.onerror = (error) => {
      console.error('WebSocket错误:', error)
      previewError.value = '连接失败，请检查摄像头状态'
      isStreaming.value = false
      previewLoading.value = false
    }
  } catch (error) {
    console.error('建立WebSocket连接失败:', error)
    previewError.value = '建立连接失败'
    previewLoading.value = false
  }
}

// 停止直播
const stopStream = () => {
  if (wsConnection.value) {
    wsConnection.value.close()
    wsConnection.value = null
  }
  isStreaming.value = false
}

// 关闭预览对话框时清理
const closePreviewDialog = () => {
  stopStream()
  previewDialogVisible.value = false
  // 清理状态
  previewImage.value = ''
  previewError.value = ''
  currentPreviewCameraId.value = null
}

// 监听对话框关闭事件
const handlePreviewDialogClose = () => {
  closePreviewDialog()
}

// 分析测试摄像头
const analysisTestCamera = (camera) => {
  currentAnalysisCameraId.value = camera.camera_id
  analysisCameraName.value = camera.camera_name
  analysisDialogVisible.value = true
}

// 开始分析测试
const startAnalysisTest = async () => {
  if (!currentAnalysisCameraId.value) return

  analysisLoading.value = true
  analysisError.value = ''
  analysisResults.value = null
  // 重置告警状态，确保每次开始分析时都能正确检测新的告警
  lastAlertState.value = ''

  try {
    // 关闭之前的连接
    stopAnalysisTest()

    // 建立WebSocket连接进行分析测试
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/api/v1/camera_infos/analysis/${currentAnalysisCameraId.value}/ws?write_to_database=${writeToDatabase.value}`
    analysisWsConnection.value = new WebSocket(wsUrl)

    analysisWsConnection.value.onopen = () => {
      console.log('分析测试WebSocket连接已建立')
      isAnalysisStreaming.value = true
      analysisLoading.value = false
    }

    // 优化WebSocket消息处理，使用requestAnimationFrame确保图像流畅更新
    let pendingUpdate = null
    
    analysisWsConnection.value.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.error) {
          analysisError.value = data.error
          isAnalysisStreaming.value = false
        } else {
          // 存储待更新的数据
          pendingUpdate = {
            image: data.image,
            timestamp: data.timestamp,
            results: data.results
          }
          
          // 如果没有正在进行的更新，启动一个
          if (!window.updateScheduled) {
            window.updateScheduled = true
            requestAnimationFrame(() => {
              if (pendingUpdate) {
                if (pendingUpdate.image) {
                  analysisImage.value = pendingUpdate.image
                  analysisTimestamp.value = pendingUpdate.timestamp
                  
                  // 计算FPS
                  const now = Date.now()
                  analysisFrameCount.value++
                  if (now - analysisLastTime.value >= 1000) {
                    analysisFps.value = analysisFrameCount.value * 1000 / (now - analysisLastTime.value)
                    analysisFrameCount.value = 0
                    analysisLastTime.value = now
                  }
                }
                if (pendingUpdate.results) {
                  analysisResults.value = pendingUpdate.results
                  
                  // 检查是否有告警并显示弹窗
                  checkForAlerts(pendingUpdate.results)
                }
                pendingUpdate = null
              }
              window.updateScheduled = false
            })
          }
        }
      } catch (error) {
        console.error('解析分析测试WebSocket消息失败:', error)
      }
    }

    analysisWsConnection.value.onclose = () => {
      console.log('分析测试WebSocket连接已关闭')
      isAnalysisStreaming.value = false
    }

    analysisWsConnection.value.onerror = (error) => {
      console.error('分析测试WebSocket错误:', error)
      analysisError.value = '连接失败，请检查摄像头状态'
      isAnalysisStreaming.value = false
      analysisLoading.value = false
    }
  } catch (error) {
    console.error('建立分析测试WebSocket连接失败:', error)
    analysisError.value = '建立连接失败'
    analysisLoading.value = false
  }
}

// 停止分析测试
const stopAnalysisTest = () => {
  console.log('停止分析测试，WebSocket状态:', analysisWsConnection.value?.readyState)
  if (analysisWsConnection.value) {
    console.log('关闭WebSocket连接')
    try {
      // 只有连接处于OPEN状态时才发送关闭
      if (analysisWsConnection.value.readyState === WebSocket.OPEN) {
        analysisWsConnection.value.close(1000, '用户停止分析')
      }
    } catch (error) {
      console.error('关闭WebSocket连接失败:', error)
    }
    analysisWsConnection.value = null
  }
  isAnalysisStreaming.value = false
  analysisResults.value = null
  analysisLoading.value = false
  // 停止警告提示音
  stopWarningSound()
  console.log('分析测试已停止')
}

// 检查分析结果是否有告警并显示弹窗
const checkForAlerts = (results) => {
  if (!results || !Array.isArray(results)) return

  // 检查是否有告警
  const alerts = []

  results.forEach(result => {
    // 跳过已关闭的检测类型（保留人员检测）
    const hiddenLabels = ['未戴安全帽', '未穿反光衣', '车辆检测', '区域入侵']
    if (hiddenLabels.includes(result.label)) return

    // 检查人员检测
    if (result.label === '人员检测') {
      const count = parseInt(result.value.replace(/[^0-9]/g, ''))
      if (count > 0) {
        alerts.push(`${result.label} (${result.value})`)
      }
    }
    // 检查火警告警
    else if ((result.label === '火焰检测' || result.label === '烟雾检测') && result.value === '检测到') {
      alerts.push(result.label)
    }
    // 检查害虫检测告警
    else if (result.label === '害虫检测' && result.value === '检测到') {
      alerts.push(result.label)
    }
    // 检查作物长势异常告警
    else if (result.label === '作物长势异常' && result.value === '检测到') {
      alerts.push(result.label)
    }
    // 检查柑橘检测提醒
    else if (result.label.includes('🍊 检测状态') && result.value.includes('✅')) {
      alerts.push(`${result.label} (${result.value})`)
    }
  })

  // 生成当前告警状态的唯一标识
  const currentAlertKey = alerts.sort().join('|')

  // 检查告警状态是否发生变化
  if (currentAlertKey !== lastAlertState.value) {
    // 清除之前的防抖定时器
    if (alertDebounceTimer.value) {
      clearTimeout(alertDebounceTimer.value)
    }

    // 设置防抖定时器
    alertDebounceTimer.value = setTimeout(() => {
      if (alerts.length > 0) {
        ElMessage({
          message: `检测到以下告警: ${alerts.join('、')}`,
          type: 'warning',
          duration: 5000,
          showClose: true
        })
        // 播放警告提示音（只播放最后一个告警对应的声音）
        playWarningSound(alerts[alerts.length - 1])
      } else {
        // 没有告警时停止声音
        stopWarningSound()
      }

      // 更新上次告警状态
      lastAlertState.value = currentAlertKey
    }, ALERT_DEBOUNCE_TIME)
  }
}

// 根据告警类型播放对应的提示音
const playWarningSound = (alertType) => {
  // 如果提示音已关闭，不播放任何声音
  if (!enableWarningSound.value) {
    stopWarningSound()
    return
  }

  // 停止之前播放的声音
  stopWarningSound()

  // 使用 Web Audio API 播放简短提示音
  try {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)()
    const oscillator = audioContext.createOscillator()
    const gainNode = audioContext.createGain()

    oscillator.connect(gainNode)
    gainNode.connect(audioContext.destination)

    // 根据告警类型设置不同的频率和音调
    let frequency = 880 // 默认频率
    let duration = 0.3 // 默认持续时间
    let oscType = 'sine'

    if (alertType.includes('火焰') || alertType.includes('烟雾') || alertType.includes('火警')) {
      // 火警：急促的双音
      frequency = 1000
      duration = 0.5
    } else if (alertType.includes('人员')) {
      // 人员检测：中等频率
      frequency = 800
      duration = 0.4
    } else if (alertType.includes('🌱') || alertType.includes('病害')) {
      // 作物病害检测：稍低频率
      frequency = 600
      duration = 0.35
    }

    oscillator.frequency.value = frequency
    oscillator.type = oscType
    gainNode.gain.value = 0.3 // 设置音量

    oscillator.start()
    oscillator.stop(audioContext.currentTime + duration)
  } catch (e) {
    console.error('播放提示音失败:', e)
  }
}

// 检查本地视频分析结果是否有告警并显示弹窗
const checkLocalVideoAlerts = (results) => {
  if (!results || !Array.isArray(results)) return

  // 检查是否有告警
  const alerts = []

  results.forEach(result => {
    // 跳过已关闭的检测类型（保留人员检测）
    const hiddenLabels = ['未戴安全帽', '未穿反光衣', '车辆检测', '区域入侵']
    if (hiddenLabels.includes(result.label)) return

    // 检查人员检测
    if (result.label === '人员检测') {
      const count = parseInt(result.value.replace(/[^0-9]/g, ''))
      if (count > 0) {
        alerts.push(`${result.label} (${result.value})`)
      }
    }
    // 检查火警告警
    else if ((result.label === '火焰检测' || result.label === '烟雾检测') && result.value === '检测到') {
      alerts.push(result.label)
    }
    // 检查害虫检测告警
    else if (result.label === '害虫检测' && result.value === '检测到') {
      alerts.push(result.label)
    }
    // 检查作物长势异常告警
    else if (result.label === '作物长势异常' && result.value === '检测到') {
      alerts.push(result.label)
    }
    // 检查柑橘检测提醒
    else if (result.label.includes('🍊 检测状态') && result.value.includes('✅')) {
      alerts.push(`${result.label} (${result.value})`)
    }
    // 检查作物病害检测
    else if (result.label.includes('🌱') && result.value.includes('检测到')) {
      alerts.push(`${result.label} (${result.value})`)
    }
  })

  // 如果有告警，显示弹窗
  if (alerts.length > 0) {
    ElMessage({
      message: `检测到以下告警: ${alerts.join('、')}`,
      type: 'warning',
      duration: 5000,
      showClose: true
    })
    // 播放警告提示音（只播放最后一个告警对应的声音）
    playWarningSound(alerts[alerts.length - 1])
  } else {
    // 没有告警时停止声音
    stopWarningSound()
  }
}

// 处理分析测试对话框关闭
const handleAnalysisDialogClose = () => {
  stopAnalysisTest()
  // 清除告警防抖定时器
  if (alertDebounceTimer.value) {
    clearTimeout(alertDebounceTimer.value)
    alertDebounceTimer.value = null
  }
  // 重置告警状态
  lastAlertState.value = ''
  analysisDialogVisible.value = false
  currentAnalysisCameraId.value = null
  analysisCameraName.value = ''
  analysisImage.value = ''
  analysisTimestamp.value = ''
  analysisError.value = ''
  analysisResults.value = null
}

// 本地视频分析相关方法
const localVideoAnalysis = async () => {
  localVideoDialogVisible.value = true
  await loadCrops() // 加载作物列表
}

// 处理视频上传
const handleVideoUpload = (file) => {
  selectedVideoFile.value = file.raw
  videoUrl.value = URL.createObjectURL(file.raw)
}

// 格式化进度条显示
const formatProgress = (percentage) => {
  return `${percentage}%`
}

// 开始本地视频分析
const startLocalVideoAnalysis = async () => {
  if (!selectedVideoFile.value) {
    ElMessage.warning('请选择视频文件')
    return
  }

  localAnalysisLoading.value = true
  try {
    // 重置分析状态
    isLocalAnalysisStarted.value = true
    analysisProgress.value = 0
    processedFrames.value = 0
    totalFrames.value = 0
    remainingTime.value = 0
    localAnalysisResults.value = []
    totalAnalysisResults.value = {
      helmet: 0,
      vest: 0,
      fire: 0,
      smoke: 0,
      person: 0,
      vehicle: 0,
      intrusion: 0
    }

    // 创建视频元素用于提取帧
    const video = document.createElement('video')
    video.src = videoUrl.value
    video.preload = 'metadata'

    // 等待视频加载完成
    await new Promise((resolve, reject) => {
      video.onloadedmetadata = resolve
      video.onerror = reject
    })

    // 获取视频总帧数（估算）
    const fps = video.fps || 30
    const duration = video.duration
    totalFrames.value = Math.floor(duration * fps)
    
    // 确保总帧数不为0
    if (totalFrames.value === 0) {
      // 如果视频时长为0，设置一个默认值
      totalFrames.value = 300 // 默认300帧
      console.warn('视频时长为0，使用默认总帧数:', totalFrames.value)
    } else {
      console.log('视频信息:', { duration, fps, totalFrames: totalFrames.value })
    }

    // 开始分析
    let currentFrame = 0
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    
    // 记录分析开始时间
    const startTime = Date.now()

    // 分析视频帧
    const analyzeFrame = async () => {
      if (!isLocalAnalysisStarted.value || currentFrame >= totalFrames.value) {
        clearInterval(analysisInterval.value)
        isLocalAnalysisStarted.value = false
        
        // 根据分析模式显示不同的报告
        let reportContent = ''
        
        if (localAnalysisForm.analysisMode === '8') {
          // 作物病害检测模式
          reportContent = `<div style="padding: 20px;">
            <h3 style="margin-bottom: 20px; color: #1890ff; text-align: center; font-size: 18px;">🌱 作物病害检测完成</h3>
            <div style="background-color: #f5f7fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
              <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">
                <div style="padding: 10px; background-color: white; border-radius: 6px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">
                  <strong style="color: #666;">分析帧数：</strong>
                  <span style="color: #1890ff; font-weight: 500;">${processedFrames.value} / ${totalFrames.value} 帧</span>
                </div>
                <div style="padding: 10px; background-color: white; border-radius: 6px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">
                  <strong style="color: #666;">作物类型：</strong>
                  <span style="color: #1890ff; font-weight: 500;">${getCropLabel(localAnalysisForm.cropType)}</span>
                </div>
                <div style="padding: 10px; background-color: white; border-radius: 6px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); grid-column: 1 / -1;">
                  <strong style="color: #666;">病害检测：</strong>
                  <span style="color: ${totalAnalysisResults.value.diseaseCount > 0 ? '#f56c6c' : '#536f88'}; font-weight: 500;">${totalAnalysisResults.value.diseaseCount} 次</span>
                </div>
              </div>
            </div>
            <div style="text-align: center; color: #999; font-size: 14px;">
              分析结果仅供参考，实际情况请以现场为准
            </div>
          </div>`
        } else {
          // 其他模式的报告
          reportContent = `<div style="padding: 20px;">
            <h3 style="margin-bottom: 20px; color: #1890ff; text-align: center; font-size: 18px;">视频分析完成</h3>
            <div style="background-color: #f5f7fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
              <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">
                <div style="padding: 10px; background-color: white; border-radius: 6px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">
                  <strong style="color: #666;">分析帧数：</strong>
                  <span style="color: #1890ff; font-weight: 500;">${processedFrames.value} / ${totalFrames.value} 帧</span>
                </div>
                <div style="padding: 10px; background-color: white; border-radius: 6px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">
                  <strong style="color: #666;">分析模式：</strong>
                  <span style="color: #1890ff; font-weight: 500;">${localAnalysisForm.analysisMode === '1' ? '全部' : localAnalysisForm.analysisMode === '2' ? '安全规范' : localAnalysisForm.analysisMode === '3' ? '区域入侵' : '火警'}</span>
                </div>
                <div style="padding: 10px; background-color: white; border-radius: 6px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">
                  <strong style="color: #666;">未戴安全帽：</strong>
                  <span style="color: ${totalAnalysisResults.value.helmet > 0 ? '#f56c6c' : '#536f88'}; font-weight: 500;">${totalAnalysisResults.value.helmet} 次</span>
                </div>
                <div style="padding: 10px; background-color: white; border-radius: 6px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">
                  <strong style="color: #666;">未穿反光衣：</strong>
                  <span style="color: ${totalAnalysisResults.value.vest > 0 ? '#f56c6c' : '#536f88'}; font-weight: 500;">${totalAnalysisResults.value.vest} 次</span>
                </div>
                <div style="padding: 10px; background-color: white; border-radius: 6px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">
                  <strong style="color: #666;">火焰检测：</strong>
                  <span style="color: ${totalAnalysisResults.value.fire > 0 ? '#f56c6c' : '#536f88'}; font-weight: 500;">${totalAnalysisResults.value.fire} 次</span>
                </div>
                <div style="padding: 10px; background-color: white; border-radius: 6px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">
                  <strong style="color: #666;">烟雾检测：</strong>
                  <span style="color: ${totalAnalysisResults.value.smoke > 0 ? '#f56c6c' : '#536f88'}; font-weight: 500;">${totalAnalysisResults.value.smoke} 次</span>
                </div>
                <div style="padding: 10px; background-color: white; border-radius: 6px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">
                  <strong style="color: #666;">人员检测：</strong>
                  <span style="color: #1890ff; font-weight: 500;">${totalAnalysisResults.value.person} 人</span>
                </div>
                <div style="padding: 10px; background-color: white; border-radius: 6px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">
                  <strong style="color: #666;">车辆检测：</strong>
                  <span style="color: #1890ff; font-weight: 500;">${totalAnalysisResults.value.vehicle} 辆</span>
                </div>
                <div style="padding: 10px; background-color: white; border-radius: 6px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); grid-column: 1 / -1;">
                  <strong style="color: #666;">区域入侵：</strong>
                  <span style="color: ${totalAnalysisResults.value.intrusion > 0 ? '#f56c6c' : '#536f88'}; font-weight: 500;">${totalAnalysisResults.value.intrusion} 次</span>
                </div>
              </div>
            </div>
            <div style="text-align: center; color: #999; font-size: 14px;">
              分析结果仅供参考，实际情况请以现场为准
            </div>
          </div>`
        }
        
        ElMessageBox.alert(reportContent, '分析完成', {
            dangerouslyUseHTMLString: true,
            confirmButtonText: '确定',
            customClass: 'total-analysis-popup',
            width: '600px'
          }).catch(() => {
          // 捕获用户关闭对话框的情况，防止未捕获的异常
        })
        return
      }

      // 设置视频当前时间
      video.currentTime = currentFrame / fps

      // 等待视频帧加载
      await new Promise(resolve => {
        video.onseeked = resolve
      })

      // 绘制当前帧到画布
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height)

      // 将画布转换为Base64
      const frameData = canvas.toDataURL('image/jpeg', 0.8)

      // 初始化病害检测计数
      if (!totalAnalysisResults.value.diseaseCount) {
        totalAnalysisResults.value.diseaseCount = 0
      }

      // 根据分析模式选择不同的API
      try {
        if (localAnalysisForm.analysisMode === '8') {
          // 模式8：作物病害检测
          // 将DataURL转换为Blob
          const response1 = await fetch(frameData)
          const blob = await response1.blob()
          
          // 创建FormData
          const formData = new FormData()
          formData.append('file', blob, 'frame.jpg')
          
          // 调用作物病害检测API
          const token = localStorage.getItem('token')
          const response = await fetch(`/api/v1/crop-disease-detection/detect?crop_type=${localAnalysisForm.cropType}&record_alarm=true`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`
            },
            body: formData
          })
          
          if (response.ok) {
            const result = await response.json()
            // 格式化结果为统一格式
            const analysisResults = []
            
            if (result.success && result.predictions) {
              analysisResults.push({
                label: `🌱 ${getCropLabel(result.crop_type)}病害检测`,
                value: `检测到 ${result.predictions.length} 个病害`
              })
              
              // 添加详细检测结果
              result.predictions.forEach((pred, index) => {
                analysisResults.push({
                  label: `病害 ${index + 1}`,
                  value: `${pred.class_name} (${(pred.confidence * 100).toFixed(1)}%)`
                })
              })
              
              // 更新病害计数
              if (result.predictions.length > 0) {
                totalAnalysisResults.value.diseaseCount++
              }
            } else {
              analysisResults.push({
                label: `🌱 ${getCropLabel(localAnalysisForm.cropType)}病害检测`,
                value: '未检测到病害'
              })
            }
            
            localAnalysisResults.value = analysisResults
            // 检查是否有告警
            if (result.success && result.predictions.length > 0) {
              checkLocalVideoAlerts(analysisResults)
            }
          }
        } else {
          // 其他模式：使用原来的分析接口
          const token = localStorage.getItem('token')
          const response = await fetch('/api/v1/camera_infos/analyze_frame', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
              image: frameData,
              analysis_mode: localAnalysisForm.analysisMode
            })
          })

          if (response.ok) {
            const result = await response.json()
            if (result.results) {
              localAnalysisResults.value = result.results
              
              // 检查是否有告警并显示提示
              checkLocalVideoAlerts(result.results)
              
              // 更新总的分析结果
              result.results.forEach(item => {
                if (item.label === '未戴安全帽' && item.value === '检测到') {
                  totalAnalysisResults.value.helmet++
                } else if (item.label === '未穿反光衣' && item.value === '检测到') {
                  totalAnalysisResults.value.vest++
                } else if (item.label === '火焰检测' && item.value === '检测到') {
                  totalAnalysisResults.value.fire++
                } else if (item.label === '烟雾检测' && item.value === '检测到') {
                  totalAnalysisResults.value.smoke++
                } else if (item.label === '人员检测') {
                  // 提取数字部分，处理"X人"格式的字符串
                  const count = parseInt(item.value.replace(/[^0-9]/g, ''))
                  if (!isNaN(count)) {
                    // 取最大值而不是累加，减少重复计数误差
                    if (count > totalAnalysisResults.value.person) {
                      totalAnalysisResults.value.person = count
                    }
                  }
                } else if (item.label === '车辆检测') {
                  // 提取数字部分，处理"X辆"格式的字符串
                  const count = parseInt(item.value.replace(/[^0-9]/g, ''))
                  if (!isNaN(count)) {
                    // 取最大值而不是累加，减少重复计数误差
                    if (count > totalAnalysisResults.value.vehicle) {
                      totalAnalysisResults.value.vehicle = count
                    }
                  }
                } else if (item.label === '区域入侵' && item.value === '检测到') {
                  totalAnalysisResults.value.intrusion++
                }
              })
            }
          }
        }
      } catch (error) {
        console.error('分析API调用错误:', error)
      }

      // 更新进度
      currentFrame += localAnalysisForm.frameInterval
      processedFrames.value = currentFrame
      analysisProgress.value = Math.min(Math.round((currentFrame / totalFrames.value) * 100), 100)
      
      // 估算剩余时间
      const elapsedTime = (Date.now() - startTime) / 1000
      const framesProcessed = Math.min(currentFrame, totalFrames.value)
      const framesRemaining = totalFrames.value - framesProcessed
      
      if (framesProcessed > 0) {
        // 计算实际处理速度（帧/秒）
        const processingSpeed = framesProcessed / elapsedTime
        // 计算剩余时间
        remainingTime.value = Math.max(0, Math.round(framesRemaining / processingSpeed))
      } else {
        // 初始阶段，使用基于帧率的估算
        remainingTime.value = Math.max(0, Math.round((totalFrames.value / fps) * 0.5))
      }
    }

    // 开始分析间隔
    analysisInterval.value = setInterval(analyzeFrame, 1000)
    
    // 立即分析第一帧
    await analyzeFrame()
  } catch (error) {
    console.error('本地视频分析失败:', error)
    ElMessage.error('分析失败，请重试')
  } finally {
    localAnalysisLoading.value = false
  }
}

// 停止本地视频分析
const stopLocalVideoAnalysis = () => {
  if (analysisInterval.value) {
    clearInterval(analysisInterval.value)
    analysisInterval.value = null
  }
  isLocalAnalysisStarted.value = false
}

// 处理本地视频分析对话框关闭
const handleLocalVideoDialogClose = () => {
  stopLocalVideoAnalysis()
  localVideoDialogVisible.value = false
  selectedVideoFile.value = null
  videoUrl.value = ''
  localAnalysisForm.analysisMode = '1'
  localAnalysisForm.frameInterval = 5
  isLocalAnalysisStarted.value = false
  analysisProgress.value = 0
  processedFrames.value = 0
  totalFrames.value = 0
  remainingTime.value = 0
  localAnalysisResults.value = []
}

// ========== 手机摄像头相关方法 ==========

// 打开手机摄像头对话框
const openPhoneCamera = async () => {
  phoneCameraDialogVisible.value = true
  await detectLocalIP()
  updatePhonePushUrl()
  await loadCrops() // 加载作物列表
}

// 检测本机IP地址
const detectLocalIP = async () => {
  try {
    // 方法1: 调用后端API获取本地IP地址
    const response = await fetch('/api/v1/camera_infos/local_ip', {
      method: 'GET'
    })
    
    if (response.ok) {
      const result = await response.json()
      if (result.code === 1 && result.data && result.data.ip) {
        localIPAddress.value = result.data.ip
        updateConnectionUrl()
        updatePhonePushUrl()
        return result.data.ip
      }
    }
    
    // 方法2: 回退到使用location.hostname
    localIPAddress.value = window.location.hostname
    updateConnectionUrl()
    updatePhonePushUrl()
    return window.location.hostname
  } catch (error) {
    console.error('检测IP地址失败:', error)
    localIPAddress.value = window.location.hostname
    updateConnectionUrl()
    updatePhonePushUrl()
    return window.location.hostname
  }
}

// 更新连接地址
const updateConnectionUrl = () => {
  const protocol = window.location.protocol
  const port = window.location.port
  const hostname = localIPAddress.value || window.location.hostname
  phoneConnectionUrl.value = `${protocol}//${hostname}${port ? ':' + port : ''}`
  generateQRCode(phoneConnectionUrl.value)
}

// 生成二维码
const generateQRCode = (url) => {
  QRCode.toDataURL(url, { width: 200, margin: 1 }, (err, dataUrl) => {
    if (err) {
      console.error('生成二维码失败:', err)
    } else {
      qrCodeUrl.value = dataUrl
    }
  })
}

// 复制本机IP
const copyLocalIP = () => {
  navigator.clipboard.writeText(localIPAddress.value).then(() => {
    ElMessage.success('IP地址已复制')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

// 复制连接地址
const copyConnectionUrl = () => {
  navigator.clipboard.writeText(phoneConnectionUrl.value).then(() => {
    ElMessage.success('连接地址已复制')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

// 处理手机摄像头对话框关闭
const handlePhoneCameraDialogClose = () => {
  stopPhoneViewer()
  stopPhoneCameraAnalysis()
  phoneCameraDialogVisible.value = false
  phoneCameraMode.value = 'phone'
  phoneViewerMirror.value = false
}

// ========== 图片分析相关方法 ==========

// 打开图片分析对话框
const imageAnalysis = () => {
  imageAnalysisDialogVisible.value = true
  // 获取作物列表
  loadCrops()
}

// 加载作物列表
const loadCrops = async () => {
  try {
    const result = await cropDiseaseApi.getCrops()
    if (result && result.success) {
      availableCrops.value = result.crops || []
    } else {
      // API调用失败时使用默认的作物列表
      availableCrops.value = ['apple', 'corn', 'cotton', 'grape', 'potato', 'rice', 'strawberry', 'tomato', 'wheat']
    }
  } catch (error) {
    console.error('获取作物列表失败:', error)
    // 出错时使用默认的作物列表
    availableCrops.value = ['apple', 'corn', 'cotton', 'grape', 'potato', 'rice', 'strawberry', 'tomato', 'wheat']
  }
}

// 获取作物类型标签
const getCropLabel = (crop) => {
  const cropLabels = {
    'apple': '苹果',
    'corn': '玉米',
    'cotton': '棉花',
    'grape': '葡萄',
    'potato': '马铃薯',
    'rice': '水稻',
    'strawberry': '草莓',
    'tomato': '番茄',
    'wheat': '小麦'
  }
  return cropLabels[crop] || crop
}

// 处理图片上传
const handleImageUpload = (file) => {
  selectedImageFile.value = file.raw
  imageUrl.value = URL.createObjectURL(file.raw)
}

// 清除选择的图片
const clearSelectedImage = () => {
  selectedImageFile.value = null
  imageUrl.value = ''
}

// 开始图片分析
const startImageAnalysis = async () => {
  if (!selectedImageFile.value) {
    ElMessage.warning('请先选择图片')
    return
  }

  imageAnalysisLoading.value = true
  try {
    let result
    if (imageAnalysisForm.analysisMode === 'cropDisease') {
      result = await cropDiseaseApi.detect(selectedImageFile.value, imageAnalysisForm.cropType)
    } else {
      result = await citrusApi.detect(selectedImageFile.value)
    }

    if (result) {
      imageAnalysisResult.value = result
      ElMessage.success('分析完成')
    }
  } catch (error) {
    console.error('图片分析失败:', error)
    ElMessage.error('分析失败，请重试')
  } finally {
    imageAnalysisLoading.value = false
  }
}

// 重置图片分析
const resetImageAnalysis = () => {
  imageAnalysisResult.value = null
}

// 处理图片分析对话框关闭
const handleImageAnalysisDialogClose = () => {
  imageAnalysisDialogVisible.value = false
  selectedImageFile.value = null
  imageUrl.value = ''
  imageAnalysisResult.value = null
  imageAnalysisForm.analysisMode = 'cropDisease'
  imageAnalysisForm.cropType = 'rice'
}

// ========== 手机摄像头分析相关方法 ==========

// 开始手机摄像头分析
const startPhoneCameraAnalysis = () => {
  if (!phoneViewerConnected.value) {
    ElMessage.warning('请先连接手机摄像头')
    return
  }
  
  isPhoneCameraAnalyzing.value = true
  phoneCameraLastAlertState.value = ''
  phoneCameraAnalysisResults.value = null
  
  // 开始分析帧
  phoneCameraAnalysisInterval.value = setInterval(analyzePhoneCameraFrame, 1500) // 每1.5秒分析一次
  
  ElMessage.success('分析已开始')
}

// 停止手机摄像头分析
const stopPhoneCameraAnalysis = () => {
  if (phoneCameraAnalysisInterval.value) {
    clearInterval(phoneCameraAnalysisInterval.value)
    phoneCameraAnalysisInterval.value = null
  }
  
  isPhoneCameraAnalyzing.value = false
  phoneCameraAnalysisResults.value = null
  phoneCameraLastFrameData.value = null
  phoneCameraLastAlertState.value = ''
}

// 分析手机摄像头当前帧
const analyzePhoneCameraFrame = async () => {
  if (!phoneViewerCanvas.value || !isPhoneCameraAnalyzing.value) return
  
  try {
    // 从Canvas获取当前帧数据
    const canvas = phoneViewerCanvas.value
    const frameData = canvas.toDataURL('image/jpeg', 0.6)
    phoneCameraLastFrameData.value = frameData
    
    // 检查分析模式
    if (phoneCameraAnalysisMode.value === '8') {
      // 模式8：作物病害检测
      // 将DataURL转换为Blob
      const response1 = await fetch(frameData)
      const blob = await response1.blob()
      
      // 创建FormData
      const formData = new FormData()
      formData.append('file', blob, 'frame.jpg')
      
      // 调用作物病害检测API（仅检测显示，不写库——避免模型误报污染数据库）
      const token = localStorage.getItem('token')
      const response = await fetch(`/api/v1/crop-disease-detection/detect?crop_type=${phoneCameraCropType.value}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      })

      if (response.ok) {
        const result = await response.json()
        // 格式化结果为统一格式
        const analysisResults = []

        if (result.success && result.predictions) {
          analysisResults.push({
            label: `🌱 ${getCropLabel(result.crop_type)}病害检测`,
            value: `检测到 ${result.predictions.length} 个病害`
          })
          
          // 添加详细检测结果
          result.predictions.forEach((pred, index) => {
            analysisResults.push({
              label: `病害 ${index + 1}`,
              value: `${pred.class_name} (${(pred.confidence * 100).toFixed(1)}%)`
            })
          })
        } else {
          analysisResults.push({
            label: `🌱 ${getCropLabel(phoneCameraCropType.value)}病害检测`,
            value: '未检测到病害'
          })
        }
        
        phoneCameraAnalysisResults.value = analysisResults
        // 检查是否有告警
        if (result.success && result.predictions.length > 0) {
          checkPhoneCameraAlerts(analysisResults)
          // ★ 直推桥接：检测到病害 → 发送到 5174
          bridgePushDetections(result.predictions, result.crop_type)
        }
      }
    } else {
      // 其他模式：使用原来的分析接口
      const token = localStorage.getItem('token')
      const response = await fetch('/api/v1/camera_infos/analyze_frame', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          image: frameData,
          analysis_mode: phoneCameraAnalysisMode.value
        })
      })
      
      if (response.ok) {
        const result = await response.json()
        if (result.results) {
          phoneCameraAnalysisResults.value = result.results
          
          // 检查是否有告警并显示提示
          checkPhoneCameraAlerts(result.results)
        }
      }
    }
  } catch (error) {
    console.error('分析手机摄像头帧失败:', error)
  }
}

// 检查手机摄像头分析结果是否有告警并显示弹窗
const checkPhoneCameraAlerts = (results) => {
  if (!results || !Array.isArray(results)) return
  
  // 检查是否有告警
  const alerts = []
  
  results.forEach(result => {
    // 跳过已关闭的检测类型（保留人员检测）
    const hiddenLabels = ['未戴安全帽', '未穿反光衣', '车辆检测', '区域入侵']
    if (hiddenLabels.includes(result.label)) return

    // 检查人员检测
    if (result.label === '人员检测') {
      const count = parseInt(result.value.replace(/[^0-9]/g, ''))
      if (count > 0) {
        alerts.push(`${result.label} (${result.value})`)
      }
    }
    // 检查火警告警
    if ((result.label === '火焰检测' || result.label === '烟雾检测') && result.value === '检测到') {
      alerts.push(result.label)
    }
    // 检查害虫检测告警
    else if (result.label === '害虫检测' && result.value === '检测到') {
      alerts.push(result.label)
    }
    // 检查作物长势异常告警
    else if (result.label === '作物长势异常' && result.value === '检测到') {
      alerts.push(result.label)
    }
    // 检查柑橘检测提醒
    else if (result.label.includes('🍊 检测状态') && result.value.includes('✅')) {
      alerts.push(`${result.label} (${result.value})`)
    }
    // 检查作物病害检测
    else if (result.label.includes('🌱') && result.value.includes('检测到')) {
      alerts.push(`${result.label} (${result.value})`)
    }
  })
  
  // 生成当前告警状态的唯一标识
  const currentAlertKey = alerts.sort().join('|')
  
  // 检查告警状态是否发生变化
  if (currentAlertKey !== phoneCameraLastAlertState.value) {
    // 更新上次告警状态
    phoneCameraLastAlertState.value = currentAlertKey
    
    // 如果有告警，显示弹窗
    if (alerts.length > 0) {
      ElMessage({
        message: `检测到以下告警: ${alerts.join('、')}`,
        type: 'warning',
        duration: 5000,
        showClose: true
      })
    }
  }
}

// ★ 直推桥接：检测到病害 → POST 到 8089 内存队列 → 5174 拉取
const bridgePushDetections = (predictions, cropType) => {
  const detections = predictions.map(p => {
    const conf = p.confidence || 0.88
    return {
      disease_type: p.class_name,
      crop: getCropLabel(cropType),
      confidence: conf,
      severity: conf >= 0.9 ? '严重' : conf >= 0.7 ? '中等' : '轻微',
      advice: `检测到${p.class_name}（${(conf * 100).toFixed(0)}%），请复核。`,
      source: '5175'
    }
  })
  fetch('/api/v1/bridge/detection', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ detections })
  }).catch(() => {})
}

// ========== 手机推流观看相关方法 ==========

// 更新连接地址
const updatePhonePushUrl = () => {
  const protocol = 'https:' // 手机访问必须用 HTTPS 才能获取摄像头
  const port = '8443' // HTTPS 后端端口
  const hostname = localIPAddress.value || window.location.hostname
  phonePushUrl.value = `${protocol}//${hostname}:${port}/phone-camera`
  generatePhonePushQRCode(phonePushUrl.value)
}

// 生成手机推流二维码（本地生成，不依赖外部API）
const generatePhonePushQRCode = (url) => {
  QRCode.toDataURL(url, { width: 200, margin: 1 }, (err, dataUrl) => {
    if (err) {
      console.error('生成二维码失败:', err)
    } else {
      phonePushQrCodeUrl.value = dataUrl
    }
  })
}

// 复制手机推流地址
const copyPhonePushUrl = () => {
  navigator.clipboard.writeText(phonePushUrl.value).then(() => {
    ElMessage.success('连接地址已复制')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

const loadImageFromBlob = (blob) => {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(blob)
    const img = new Image()
    img.onload = () => {
      URL.revokeObjectURL(url)
      resolve(img)
    }
    img.onerror = (err) => {
      URL.revokeObjectURL(url)
      reject(err)
    }
    img.src = url
  })
}

const drawPhoneViewerFrame = async (blob) => {
  if (phoneViewerRenderBusy.value) {
    phoneViewerQueuedFrame.value = blob
    return
  }

  phoneViewerRenderBusy.value = true
  const t0 = performance.now()
  let source = null
  let closeSource = null

  try {
    if (window.createImageBitmap) {
      source = await createImageBitmap(blob)
      closeSource = () => source.close()
    } else {
      source = await loadImageFromBlob(blob)
    }

    const sourceWidth = source.width || source.naturalWidth
    const sourceHeight = source.height || source.naturalHeight
    const canvas = phoneViewerCanvas.value
    if (!canvas || !sourceWidth || !sourceHeight) return

    const ctx = canvas.getContext('2d')
    const container = canvas.parentElement
    const containerRect = container.getBoundingClientRect()
    const dpr = Math.min(window.devicePixelRatio || 1, 2)
    const canvasWidth = Math.max(1, Math.round(containerRect.width * dpr))
    const canvasHeight = Math.max(1, Math.round(containerRect.height * dpr))

    if (canvas.width !== canvasWidth || canvas.height !== canvasHeight) {
      canvas.width = canvasWidth
      canvas.height = canvasHeight
    }

    ctx.fillStyle = '#000'
    ctx.fillRect(0, 0, canvas.width, canvas.height)

    const scale = Math.min(canvas.width / sourceWidth, canvas.height / sourceHeight)
    const drawWidth = sourceWidth * scale
    const drawHeight = sourceHeight * scale
    const drawX = (canvas.width - drawWidth) / 2
    const drawY = (canvas.height - drawHeight) / 2

    ctx.drawImage(source, drawX, drawY, drawWidth, drawHeight)

    phoneViewerFrameCount.value++
    phoneViewerLatency.value = Math.round(performance.now() - t0)
    phoneViewerResolution.value = `${sourceWidth}×${sourceHeight}`
  } catch (error) {
    console.error('渲染手机摄像头帧失败:', error)
  } finally {
    if (closeSource) closeSource()
    phoneViewerRenderBusy.value = false

    if (phoneViewerQueuedFrame.value) {
      const nextFrame = phoneViewerQueuedFrame.value
      phoneViewerQueuedFrame.value = null
      drawPhoneViewerFrame(nextFrame)
    }
  }
}

// 开始手机推流观看
const startPhoneViewer = () => {
  try {
    // 先关闭旧的连接
    if (phoneViewerWs.value) {
      try {
        phoneViewerWs.value.close()
      } catch (e) {
        console.log('关闭旧连接失败:', e)
      }
      phoneViewerWs.value = null
    }

    // 通过 Vite 代理连接，避免浏览器拦截自签名 WSS
    const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/v1/camera_infos/phone_camera/viewer`

    console.log('开始连接手机摄像头观看端(直连):', wsUrl)
    phoneViewerWs.value = new WebSocket(wsUrl)
    
    phoneViewerWs.value.onopen = () => {
      console.log('手机摄像头观看端连接成功')
      phoneViewerConnected.value = true
      ElMessage.success('已连接到手机摄像头')
      startPhoneViewerFpsCounter()
    }
    
    phoneViewerWs.value.onmessage = (event) => {
      if (event.data instanceof Blob) {
        drawPhoneViewerFrame(event.data)
      } else {
        // 文本数据是JSON
        try {
          // 检查是否为空字符串（手机端保活消息）
          if (!event.data || event.data.trim() === '') {
            console.log('收到保活消息，忽略')
            return
          }
          const data = JSON.parse(event.data)
          console.log('收到JSON数据:', data)
          if (data.type === 'phone_connected') {
            if (data.meta) {
              phoneViewerResolution.value = `${data.meta.width || '?'}×${data.meta.height || '?'}`
              // 检查是否有位置信息
              if (data.meta.location) {
                phoneCameraLocation.value = {
                  latitude: data.meta.location.latitude,
                  longitude: data.meta.location.longitude
                }
                console.log('收到手机位置信息:', phoneCameraLocation.value)
                // 发送事件通知地图页面
                window.dispatchEvent(new CustomEvent('phoneCameraLocationUpdate', {
                  detail: phoneCameraLocation.value
                }))
                ElMessage.success('已获取手机位置信息')
              }
            }
          } else if (data.type === 'phone_disconnected') {
            ElMessage.warning('手机已断开连接')
            // 清除位置信息
            phoneCameraLocation.value = null
            window.dispatchEvent(new CustomEvent('phoneCameraLocationUpdate', {
              detail: null
            }))
          }
        } catch (e) {
          console.error('解析JSON失败:', e)
          // 不是JSON，忽略
        }
      }
    }
    
    phoneViewerWs.value.onclose = (event) => {
      console.log('手机摄像头观看端连接关闭:', event)
      phoneViewerConnected.value = false
      stopPhoneViewerFpsCounter()
      if (event.code !== 1000) {
        const hostname = localIPAddress.value || window.location.hostname
        ElMessage.warning({
          message: `连接断开(code:${event.code})。请先在浏览器新标签页打开 https://${hostname}:8443 信任自签名证书后重试`,
          duration: 8000
        })
      } else {
        ElMessage.info('已断开连接')
      }
    }

    phoneViewerWs.value.onerror = (error) => {
      console.error('手机观看WebSocket错误:', error)
      const hostname = localIPAddress.value || window.location.hostname
      ElMessage.error({
        message: `WSS连接失败。请先在浏览器新标签页打开 https://${hostname}:8443 信任自签名证书`,
        duration: 8000
      })
    }
  } catch (error) {
    console.error('建立手机观看连接失败:', error)
    ElMessage.error('连接失败')
  }
}

// 停止手机推流观看
const stopPhoneViewer = () => {
  if (phoneViewerWs.value) {
    try {
      phoneViewerWs.value.close()
    } catch (e) {}
    phoneViewerWs.value = null
  }
  phoneViewerConnected.value = false
  stopPhoneViewerFpsCounter()
  phoneViewerResolution.value = ''
  phoneViewerFps.value = 0
  phoneViewerLatency.value = 0
  phoneViewerFrameCount.value = 0
  phoneViewerRenderBusy.value = false
  phoneViewerQueuedFrame.value = null
  
  // 清空Canvas
  const canvas = phoneViewerCanvas.value
  if (canvas) {
    const ctx = canvas.getContext('2d')
    ctx.clearRect(0, 0, canvas.width, canvas.height)
  }
}

// 切换镜像
const togglePhoneViewerMirror = () => {
  phoneViewerMirror.value = !phoneViewerMirror.value
}

// 开始FPS计数
const startPhoneViewerFpsCounter = () => {
  phoneViewerLastTime.value = Date.now()
  phoneViewerFrameCount.value = 0
  
  const updateFps = () => {
    if (!phoneViewerConnected.value) return
    
    const now = Date.now()
    if (now - phoneViewerLastTime.value >= 1000) {
      phoneViewerFps.value = phoneViewerFrameCount.value
      phoneViewerFrameCount.value = 0
      phoneViewerLastTime.value = now
    }
    
    phoneViewerFpsInterval.value = requestAnimationFrame(updateFps)
  }
  
  phoneViewerFpsInterval.value = requestAnimationFrame(updateFps)
}

// 停止FPS计数
const stopPhoneViewerFpsCounter = () => {
  if (phoneViewerFpsInterval.value) {
    cancelAnimationFrame(phoneViewerFpsInterval.value)
    phoneViewerFpsInterval.value = null
  }
}

const submitCamera = async () => {
  if (!cameraFormRef.value) return
  
  try {
    const valid = await cameraFormRef.value.validate()
    if (valid) {
      submitLoading.value = true
      try {
        let result
        // 准备提交的数据
        const submitData = {
          ...cameraForm,
          park_area_id: parseInt(cameraForm.park_area_id),
          analysis_mode: parseInt(cameraForm.analysis_mode)
        }
        
        if (isEdit.value) {
          // 编辑摄像头
          console.log('编辑摄像头，ID:', cameraForm.camera_info_id)
          result = await cameraStore.updateCamera(parseInt(cameraForm.camera_info_id), submitData)
        } else {
          // 添加摄像头
          result = await cameraStore.createCamera(submitData)
        }
        
        if (result.success) {
          dialogVisible.value = false
          // 重新获取列表和状态统计
          await fetchCameras()
          await cameraStore.fetchStatusReport()
        }
      } catch (error) {
        console.error('保存摄像头失败:', error)
      } finally {
        submitLoading.value = false
      }
    }
  } catch (error) {
    console.error('表单验证失败:', error)
  }
}

// 生命周期
onMounted(async () => {
  await fetchAreas()
  await cameraStore.fetchStatusReport()
  await fetchCameras()
  await loadCrops() // 加载作物列表
})
</script>

<style scoped>
.cameras {
  padding: 20px;
  width: 100%;
  background-color: #f5f7fa;
  min-height: 100vh;
  box-sizing: border-box;
}

/* 搜索卡片样式优化 */
.search-card {
  margin-bottom: 20px;
  border-radius: 12px;
  border: 1px solid #e4e7ed;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  overflow: hidden;
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
}

.search-card:hover {
  box-shadow: 0 4px 16px 0 rgba(0, 0, 0, 0.08);
}

.search-card :deep(.el-card__body) {
  padding: 20px 24px;
}

/* 搜索表单样式 */
.search-card :deep(.el-form) {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
}

.search-card :deep(.el-form-item) {
  margin-bottom: 0;
  margin-right: 0;
}

.search-card :deep(.el-form-item__label) {
  font-weight: 500;
  color: #606266;
  font-size: 14px;
  padding-right: 12px;
}

/* 输入框样式优化 */
.search-card :deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease;
}

.search-card :deep(.el-input__wrapper:hover) {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.08);
}

.search-card :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #536f88, 0 4px 8px rgba(83, 111, 136, 0.15);
}

/* 选择器样式优化 */
.search-card :deep(.el-select .el-input__wrapper) {
  border-radius: 8px;
}

/* 按钮组样式 */
.search-card :deep(.el-button) {
  border-radius: 8px;
  padding: 10px 20px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.search-card :deep(.el-button--primary) {
  background: linear-gradient(135deg, #536f88 0%, #6f879c 100%);
  border: none;
  box-shadow: 0 4px 12px rgba(83, 111, 136, 0.3);
}

.search-card :deep(.el-button--primary:hover) {
  background: linear-gradient(135deg, #6f879c 0%, #536f88 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(83, 111, 136, 0.4);
}

.search-card :deep(.el-button--success) {
  background: linear-gradient(135deg, #536f88 0%, #6f879c 100%);
  border: none;
  box-shadow: 0 4px 12px rgba(103, 194, 58, 0.3);
}

.search-card :deep(.el-button--success:hover) {
  background: linear-gradient(135deg, #6f879c 0%, #536f88 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(103, 194, 58, 0.4);
}

.search-card :deep(.el-button:not(.el-button--primary):not(.el-button--success):hover) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.status-card {
  margin-bottom: 20px;
  border-radius: 12px;
  border: 1px solid #e4e7ed;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  overflow: hidden;
  padding: 20px;
}

.status-card:hover {
  box-shadow: 0 4px 16px 0 rgba(0, 0, 0, 0.08);
}

.status-stats {
  display: flex;
  justify-content: space-around;
  flex-wrap: wrap;
  gap: 20px;
}

.stat-item {
  text-align: center;
  padding: 20px;
  background-color: #ffffff;
  border-radius: 12px;
  border: 1px solid #e4e7ed;
  box-shadow: 0 2px 8px 0 rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  min-width: 150px;
  flex: 1;
}

.stat-item:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px 0 rgba(0, 0, 0, 0.1);
}

.stat-label {
  color: #606266;
  font-size: 0.9rem;
  margin-bottom: 10px;
  font-weight: 500;
}

.stat-value {
  font-size: 2rem;
  font-weight: 600;
  color: #303133;
  transition: all 0.3s ease;
}

.stat-item:hover .stat-value {
  transform: scale(1.05);
}

.stat-value.online {
  color: #536f88;
}

.stat-value.offline {
  color: #f56c6c;
}

.table-card {
  margin-bottom: 20px;
  border-radius: 12px;
  border: 1px solid #e4e7ed;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  overflow: hidden;
}

.table-card:hover {
  box-shadow: 0 4px 16px 0 rgba(0, 0, 0, 0.08);
}

.table-card :deep(el-table) {
  border-radius: 8px;
  overflow: hidden;
}

.table-card :deep(el-table__header-wrapper) {
  background-color: #f5f7fa;
}

.table-card :deep(el-table th) {
  font-weight: 600;
  background-color: #f5f7fa !important;
  border-bottom: 1px solid #e4e7ed;
  padding: 12px 0;
}

.table-card :deep(el-table tr) {
  transition: all 0.3s ease;
}

.table-card :deep(el-table tr:hover) {
  background-color: #f5f7fa !important;
}

.table-card :deep(el-table td) {
  border-bottom: 1px solid #ebeef5;
  padding: 12px 0;
}

.table-card :deep(el-button) {
  border-radius: 6px;
  transition: all 0.3s ease;
  margin-right: 8px;
}

.table-card :deep(el-button:hover) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px 0 rgba(83, 111, 136, 0.3);
}

.table-card :deep(el-tag) {
  border-radius: 6px;
  font-size: 0.75rem;
  padding: 2px 8px;
}

.dialog-footer {
  text-align: right;
}

/* 响应式设计 */
@media screen and (max-width: 768px) {
  .cameras {
    padding: 10px;
  }
  
  .search-card {
    padding: 10px;
  }
  
  .status-card {
    padding: 10px;
  }
  
  .stat-item {
    padding: 15px;
    min-width: 120px;
  }
  
  .stat-value {
    font-size: 1.5rem;
  }
  
  .table-card {
    padding: 10px;
  }
  
  .table-card :deep(el-button) {
    margin-right: 4px;
    padding: 4px 8px;
    font-size: 12px;
  }
  
  .pagination {
    padding: 10px;
    margin-top: 10px;
  }
  
  .pagination :deep(.el-pagination) {
    flex-wrap: wrap;
    gap: 6px;
  }
  
  .pagination :deep(.el-pagination__sizes) {
    margin-right: 0;
  }
  
  .pagination :deep(.el-select .el-input) {
    width: 90px;
    min-width: 90px;
  }
  
  .pagination :deep(.el-pagination__page) {
    width: 28px;
    height: 28px;
    font-size: 12px;
  }
  
  .pagination :deep(.el-pagination__prev),
  .pagination :deep(.el-pagination__next) {
    width: 28px;
  }
}

/* 本地视频分析样式 */
.local-video-analysis {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.video-upload-section {
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 8px;
  border: 1px dashed #d9d9d9;
}

.selected-file {
  margin-top: 10px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.analysis-process-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* FPS指示器样式 */
.fps-indicator {
  margin-top: 8px;
  font-size: 14px;
  color: #536f88;
  font-weight: 500;
}

.video-player {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.progress-section {
  margin: 10px 0;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 14px;
  color: #606266;
}

.local-video-analysis .analysis-results {
  margin-top: 20px;
  padding: 16px;
  background-color: #f8f9fa;
  border-radius: 8px;
}

.local-video-analysis .analysis-results h3,
.local-video-analysis .total-analysis-results h3 {
  margin-top: 0;
  margin-bottom: 16px;
  color: #303133;
  font-size: 16px;
  font-weight: 500;
}

.local-video-analysis .total-analysis-results {
  margin-top: 20px;
  padding: 16px;
  background-color: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

@media screen and (max-width: 768px) {
  .local-video-analysis {
    gap: 10px;
  }
  
  .video-upload-section {
    padding: 10px;
  }
  
  .video-player video {
    max-height: 200px;
  }
  
  .progress-info {
    flex-direction: column;
    gap: 4px;
  }
  
  .pagination :deep(.el-pagination__jump .el-input) {
    width: 70px;
  }
}

/* 分析测试样式 */
.analysis-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
}

.preview-image-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
}

.preview-image {
  max-width: 100%;
  max-height: 400px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.preview-info {
  width: 100%;
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.streaming-indicator {
  margin-top: 10px;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.analysis-results {
  margin-top: 20px;
}

.analysis-results h4 {
  margin-bottom: 12px;
  color: #303133;
  font-weight: 500;
}

.analysis-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
  margin-top: 12px;
}

.analysis-item {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.analysis-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.analysis-item.warning {
  background-color: #fdf6ec;
  border-left: 4px solid #c58a45;
}

.analysis-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 4px;
}

.analysis-value {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.analysis-item.warning .analysis-value {
  color: #c58a45;
}

.preview-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
  color: #606266;
}

.preview-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
  color: #f56c6c;
}

/* 响应式设计 */
@media screen and (max-width: 768px) {
  .analysis-container {
    padding: 10px;
  }
  
  .preview-image {
    max-height: 300px;
  }
  
  .preview-info {
    padding: 15px;
  }
  
  .analysis-grid {
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 10px;
  }
  
  .analysis-item {
    padding: 12px;
  }
  
  .analysis-label {
    font-size: 12px;
  }
  
  .analysis-value {
    font-size: 14px;
  }
}

@media screen and (max-width: 480px) {
  .status-stats {
    flex-direction: column;
    gap: 10px;
  }
  
  .stat-item {
    width: 100%;
  }
  
  .table-card :deep(el-table th),
  .table-card :deep(el-table td) {
    padding: 8px 0;
    font-size: 12px;
  }
  
  .table-card :deep(el-button) {
    margin-right: 2px;
    padding: 2px 6px;
    font-size: 11px;
  }
}

/* 分页器样式 */
.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: 12px 16px;
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.pagination :deep(.el-pagination) {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pagination :deep(.el-pagination__sizes) {
  margin-right: 8px;
}

.pagination :deep(.el-select .el-input) {
  width: 100px;
  border-radius: 6px;
  border: 1px solid #dcdfe6;
  transition: all 0.2s ease;
  min-width: 100px;
}

.pagination :deep(.el-select .el-input__inner) {
  text-align: center;
  font-size: 14px;
  color: #303133;
  padding: 0 20px 0 12px;
}

.pagination :deep(.el-select .el-input__suffix) {
  right: 8px;
}

.pagination :deep(.el-select .el-input:hover) {
  border-color: #536f88;
  box-shadow: 0 0 0 2px rgba(83, 111, 136, 0.2);
}

.pagination :deep(.el-select .el-input.is-focus) {
  border-color: #536f88;
  box-shadow: 0 0 0 2px rgba(83, 111, 136, 0.2);
}

.pagination :deep(.el-select-dropdown) {
  border-radius: 8px;
  border: 1px solid #dcdfe6;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  overflow: hidden;
}

.pagination :deep(.el-select-dropdown__item) {
  padding: 8px 16px;
  transition: all 0.2s ease;
  border-radius: 0;
}

.pagination :deep(.el-select-dropdown__item:hover) {
  background-color: #eef2f5;
  color: #536f88;
}

.pagination :deep(.el-select-dropdown__item.selected) {
  background-color: #eef2f5;
  color: #536f88;
  font-weight: 500;
}

.pagination :deep(.el-select-dropdown__item.hover) {
  background-color: #eef2f5;
  color: #536f88;
}

.pagination :deep(.el-pagination__total) {
  font-size: 14px;
  color: #606266;
  font-weight: 400;
}

.pagination :deep(.el-pagination__prev),
.pagination :deep(.el-pagination__next) {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  border: 1px solid #dcdfe6;
  background-color: #ffffff;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pagination :deep(.el-pagination__prev:hover),
.pagination :deep(.el-pagination__next:hover) {
  border-color: #536f88;
  color: #536f88;
  box-shadow: 0 2px 8px rgba(83, 111, 136, 0.15);
}

.pagination :deep(.el-pagination__prev.is-disabled),
.pagination :deep(.el-pagination__next.is-disabled) {
  border-color: #ebeef5;
  color: #c0c4cc;
  cursor: not-allowed;
}

.pagination :deep(.el-pagination__page) {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  border: 1px solid #dcdfe6;
  background-color: #ffffff;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 2px;
}

.pagination :deep(.el-pagination__page:hover) {
  border-color: #536f88;
  color: #536f88;
}

.pagination :deep(.el-pagination__page.is-current) {
  background-color: #536f88;
  border-color: #536f88;
  color: #ffffff;
  font-weight: 500;
  box-shadow: 0 2px 8px rgba(83, 111, 136, 0.3);
}

.pagination :deep(.el-pagination__page.is-current:hover) {
  background-color: #6f879c;
  border-color: #6f879c;
}

.pagination :deep(.el-pagination__jump) {
  font-size: 14px;
  color: #606266;
  display: flex;
  align-items: center;
  gap: 8px;
}

.pagination :deep(.el-pagination__jump .el-input) {
  width: 80px;
}

.pagination :deep(.el-pagination__jump .el-input__wrapper) {
  border-radius: 6px;
}

/* 响应式设计 */
@media screen and (max-width: 768px) {
  .pagination {
    flex-direction: column;
    align-items: flex-end;
    gap: 10px;
  }
  
  .pagination :deep(.el-pagination) {
    flex-wrap: wrap;
    justify-content: flex-end;
  }
  
  .pagination :deep(.el-pagination__sizes) {
    margin-right: 0;
  }
}

/* 预览对话框样式 */
.preview-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  background-color: #f5f7fa;
  border-radius: 8px;
  padding: 20px;
}

.preview-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
  color: #909399;
}

.preview-image-wrapper {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
}

.preview-image {
  max-width: 100%;
  max-height: 480px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.preview-info {
  text-align: center;
  color: #606266;
  font-size: 14px;
}

.preview-info p {
  margin: 5px 0;
}

.preview-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
  color: #f56c6c;
}

.streaming-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  margin-top: 10px;
  padding: 4px 12px;
  border-radius: 12px;
  background-color: rgba(103, 194, 58, 0.1);
}

.streaming-indicator :deep(.el-icon) {
  font-size: 14px;
}

/* 分析结果弹窗样式 */
:deep(.total-analysis-popup) {
  border-radius: 8px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
}

:deep(.total-analysis-popup .el-message-box__header) {
  background-color: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
  border-radius: 8px 8px 0 0;
}

:deep(.total-analysis-popup .el-message-box__title) {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

:deep(.total-analysis-popup .el-message-box__content) {
  padding: 0;
}

:deep(.total-analysis-popup .el-message-box__btns) {
  padding: 15px 20px;
  background-color: #f5f7fa;
  border-top: 1px solid #e4e7ed;
  border-radius: 0 0 8px 8px;
  justify-content: center;
}

:deep(.total-analysis-popup .el-button--primary) {
  background-color: #1890ff;
  border-color: #1890ff;
  font-weight: 500;
  padding: 8px 24px;
}

:deep(.total-analysis-popup .el-button--primary:hover) {
  background-color: #40a9ff;
  border-color: #40a9ff;
}

/* ========== 手机摄像头样式 ========== */

:deep(.phone-camera-dialog) {
  --el-dialog-margin-top: 0;
  margin-top: 0;
  max-height: 78vh;
  display: flex;
  flex-direction: column;
}

:deep(.el-overlay-dialog:has(.phone-camera-dialog)) {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  overflow: hidden;
  padding-top: 3vh;
  padding-bottom: 3vh;
}

:deep(.phone-camera-dialog .el-dialog__header) {
  flex: 0 0 auto;
}

:deep(.phone-camera-dialog .el-dialog__body) {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  padding-top: 12px;
  padding-bottom: 12px;
}

:deep(.phone-camera-dialog .el-dialog__footer) {
  flex: 0 0 auto;
  border-top: 1px solid #e4e7ed;
  padding-top: 12px;
  padding-bottom: 12px;
}

.phone-camera-pc-mode,
.phone-camera-phone-mode,
.phone-camera-phone-viewer-mode {
  padding: 10px;
}

.phone-viewer-canvas {
  width: 100%;
  height: 100%;
  display: block;
  background-color: #000;
}

.video-container-wrapper {
  position: relative;
  width: 100%;
  min-height: 400px;
  background-color: #000;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 20px;
}

.video-container {
  width: 100%;
  height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #000;
  overflow: hidden;
}

.video-container.mirror {
  transform: scaleX(-1);
}

.phone-camera-video {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.phone-camera-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 15px;
  color: #909399;
}

.phone-camera-placeholder p {
  margin: 0;
  font-size: 14px;
}

.phone-camera-controls {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.phone-camera-info {
  margin-top: 10px;
}

.connection-info {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-bottom: 25px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.info-label {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
  min-width: 100px;
}

.qr-code-section {
  text-align: center;
  padding: 16px;
  background-color: #f8f9fa;
  border-radius: 8px;
  margin-bottom: 16px;
}

.qr-code-section h4 {
  margin-top: 0;
  margin-bottom: 15px;
  color: #303133;
}

.qr-code-wrapper {
  display: flex;
  justify-content: center;
}

.qr-code {
  width: 180px;
  height: 180px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.instructions {
  padding: 16px;
  background-color: #f0f9ff;
  border-radius: 8px;
  border: 1px solid #b3d8ff;
}

.instructions h4 {
  margin-top: 0;
  margin-bottom: 15px;
  color: #536f88;
}

.instructions ol {
  margin: 0;
  padding-left: 20px;
  color: #606266;
}

.instructions li {
  margin-bottom: 10px;
  line-height: 1.6;
}

/* 手机摄像头对话框响应式设计 */
@media screen and (max-width: 768px) {
  :deep(.phone-camera-dialog) {
    width: calc(100vw - 24px) !important;
    max-height: 84vh;
  }

  :deep(.el-overlay-dialog:has(.phone-camera-dialog)) {
    padding-top: 2vh;
    padding-bottom: 2vh;
  }

  .video-container-wrapper {
    min-height: 300px;
  }
  
  .video-container {
    height: 300px;
  }
  
  .phone-camera-controls {
    gap: 8px;
  }
  
  .info-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 5px;
  }
  
  .qr-code {
    width: 150px;
    height: 150px;
  }
}
</style>
