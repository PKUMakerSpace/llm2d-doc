# 前端技术架构 React + Vite
## 技术选型说明

本项目采用现代化前端技术栈：

- **React (v18)** - 用于构建用户界面
- **Vite (v6)** - 作为构建工具，提供快速开发体验
- **PixiJS (v6)** - WebGL渲染引擎，用于高性能图形渲染
- **pixi-live2d-display (v0.4)** - 专门用于在PixiJS中展示Live2D模型的插件

### 为什么选择这些技术

1. **Vite** - 提供极快的冷启动和热更新，优化开发体验
2. **PixiJS** - 专业的2D WebGL渲染库，能高效处理Live2D模型的复杂渲染需求
3. **pixi-live2d-display** - 专门为Live2D模型设计的渲染插件，简化了模型集成过程
This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react/README.md) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

前端项目结构如下：

## 项目结构

当前前端项目位于 `Geek-agent-live2D-main/frontend` 目录下，主要结构包括：

- `public/` - 静态资源目录
  - `libs/` - 第三方库文件
  - `models/` - Live2D模型文件
  - `runtime/` - 运行时相关文件
- `src/` - 源代码目录
  - `components/` - React组件
  - [App.css](./src/App.css) - 主应用样式
  - [App.jsx](./src/App.jsx) - 主应用组件
  - [index.css](./src/index.css) - 全局样式
  - [main.jsx](./src/main.jsx) - 应用入口文件
- [index.html](./index.html) - HTML模板文件
- [package.json](./node_modules/@babel/core/package.json) - 项目依赖和脚本配置
- [vite.config.js](./vite.config.js) - Vite构建配置

## 项目结构优化方法
一个好的前端应该包含以下文件夹
- `public/` - 静态资源目录
  - `libs/` - 第三方库文件
  - `models/` - Live2D模型文件
  - `runtime/` - 运行时相关文件
- `src/` - 源代码目录
  - `components/` 
    - `Webpage/` - 网页组件
    - [Live2DModel.jsx](./components/Live2DModel.jsx) - Live2D交互组件
    - LoadingDots - 加载中动画
  - `pages/` - 页面组件
    - `Webpage.jsx` - 主页组件
  - [App.css](./src/App.css) - 主应用样式
  - [App.jsx](./src/App.jsx) - 主应用组件
  - [index.css](./src/index.css) - 全局样式
  - [main.jsx](./src/main.jsx) - 应用入口文件
- [index.html](./index.html) - HTML模板文件
- [package.json](./node_modules/@babel/core/package.json) - 项目依赖和脚本配置
- [vite.config.js](./vite.config.js) - Vite构建配置

组织逻辑是

## 核心依赖

主要使用的技术栈包括：
- React (v18)
- PixiJS (v6) 和 pixi-live2d-display (v0.4) 用于渲染Live2D模型
- Vite (v6) 作为构建工具

## 主要功能

从 [App.jsx](./src/App.jsx) 文件可以看出，前端主要实现以下功能：

1. **Live2D模型展示** - 使用PixiJS和pixi-live2d-display加载和显示Live2D模型
2. **聊天交互** - 用户可以输入消息与AI角色对话
3. **表情控制** - 根据AI回复切换模型表情
4. **语音播放** - 支持TTS语音合成功能
5. **字幕显示** - 消息内容以字幕形式展示

## 通信方式

前端通过API与后端通信：
- `/api/chat` - 发送聊天消息
- `/api/upload` - 上传文件

整体采用现代化的React + Vite技术栈，专注于提供Live2D角色交互体验。

# React组件: Live2DDisplay
这是一个用于在React应用中显示和控制Live2D模型的组件，名为 [Live2DDisplay](./src/components/Live2DModel.jsx#L7-L153)。让我来详细解读这个组件：

## 组件概述

这是一个使用 [pixi.js](./node_modules/pixi.js/dist/cjs/pixi.js) 和 `pixi-live2d-display` 库实现的React组件，用于加载和显示Live2D模型，并提供控制模型表情和交互的功能。

## 主要功能

### 1. Live2D模型加载与显示
- 使用 `PIXI.Application` 创建Canvas渲染环境
- 通过 `Live2DModel.from()` 方法异步加载Live2D模型文件
- 自动调整模型大小和位置以适应屏幕
- 支持模型点击交互（`hit` 事件）

### 2. 表情控制功能
- 定义了表情映射对象 `EXPRESSIONS`，将中文表情名称映射到内部参数ID
- 提供 `showExpression()` 方法供父组件调用，用于切换模型表情
- 表情自动复位：10秒后自动将表情重置为默认状态

### 3. 交互控制
- 提供 `setTracking()` 方法控制模型是否启用自动交互
- 可控制模型是否响应鼠标移动和点击

## 核心实现细节

### Refs和状态管理
```javascript
const pixiContainerRef = useRef(null)  // PIXI容器的DOM引用
const appRef = useRef(null)            // PIXI应用实例引用
const modelRef = useRef(null)          // Live2D模型实例引用
```

### 表情映射
```javascript
const EXPRESSIONS = {
  '吐舌': 'key2',
  '黑脸': 'key3',
  '眼泪': 'key4',
  // ... 其他表情映射
}
```

### 对外暴露的方法
通过 [useImperativeHandle](./node_modules/@types/react/index.d.ts#L2055-L2055) 向父组件暴露以下方法：
1. `showExpression(expression, active)` - 显示指定表情
2. `setTracking(enabled)` - 启用/禁用模型跟踪功能

### 模型加载和渲染
- 使用 [useLayoutEffect](./node_modules/@types/react/index.d.ts#L2034-L2034) 在组件挂载时初始化PIXI应用和加载模型
- 实现了适当的清理机制，防止内存泄漏
- 模型居中显示并根据屏幕大小自动缩放

## 使用方式

父组件可以通过ref调用该组件提供的方法：
```javascript
// 显示"生气"表情
live2dRef.current.showExpression('生气')

// 启用模型跟踪
live2dRef.current.setTracking(true)
```

## 特殊处理

1. **内存管理**：组件卸载时正确清理PIXI应用和模型资源
2. **异步加载保护**：检查组件是否已卸载，避免在加载完成后执行无效操作
3. **错误处理**：对模型加载过程中的错误进行捕获和记录

这是一个功能完整的Live2D模型展示组件，适用于需要在网页中嵌入交互式虚拟角色的应用场景。

# 主应用 App.jsx
根据提供的代码，主应用 [App.jsx](./src/App.jsx) 通过以下方式调用和使用 [Live2DDisplay](./src/components/Live2DModel.jsx#L7-L153)（即Live2DModel）组件：

## 1. 组件引入和引用

```javascript
import Live2DDisplay from './components/Live2DModel'
const live2dRef = useRef(null)
```

- 使用 `import` 语句引入 [Live2DDisplay](./src/components/Live2DModel.jsx#L7-L153) 组件
- 使用 [useRef](./node_modules/@types/react/index.d.ts#L2020-L2020) 创建 [live2dRef](./src/App.jsx#L9-L9) 用于获取组件实例

## 2. 组件渲染

```jsx
<Live2DDisplay ref={live2dRef} />
```

在JSX中渲染组件，并将 [live2dRef](./src/App.jsx#L9-L9) 作为 [ref](./node_modules/@types/react/index.d.ts#L362-L362) 属性传递给组件，这样就可以通过 `live2dRef.current` 访问组件暴露的方法。

## 3. 方法调用

主应用通过 `live2dRef.current` 调用 [Live2DModel](./src/components/Live2DModel.jsx#L7-L153) 组件暴露的两个主要方法：

### 1. 显示表情

```javascript
// 在 handleSubmit 函数中
if (data.expression && live2dRef.current) {
  live2dRef.current.showExpression(data.expression)
}
```

当从后端接收到AI回复的表情信息时，调用 `showExpression` 方法显示对应的表情。

### 2. 重置表情

```javascript
// 在 playSentences 函数中
if (live2dRef.current) {
  setTimeout(() => {
    live2dRef.current.showExpression('', false)
  }, 1000)
}
```

在对话结束后，调用 `showExpression` 方法重置模型表情。

## 4. 完整调用流程

1. **初始化**：组件挂载时自动加载Live2D模型
2. **接收响应**：从后端API获取AI回复和表情信息
3. **显示表情**：调用 `live2dRef.current.showExpression(data.expression)` 显示指定表情
4. **重置表情**：在对话结束后调用 `live2dRef.current.showExpression('', false)` 重置表情

## 5. 调用时机

- **显示表情**：在 [handleSubmit](./src/App.jsx#L135-L232) 函数中，收到后端响应后立即调用
- **重置表情**：在 [playSentences](./src/App.jsx#L25-L133) 函数中，所有语音播放完毕后调用

这种设计使得主应用可以控制Live2D模型的表情变化，增强了用户与AI交互的视觉体验。