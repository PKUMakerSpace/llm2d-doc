# 前端说明文档
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
  - `assets/` - 需要插入的资源目录
  - `components/` - React组件
    - `Chat/` - 聊天组件
      - [InputArea.jsx](./src/components/Chat/InputArea.jsx)
      - [MessageList.jsx](./src/components/Chat/MessageList.jsx)
    - `Live2D/` - Live2D 组件
      - [Live2DController.jsx](./src/components/Live2D/Live2DController.jsx) - Live2D模型控制器组件
      - [Live2DModel.jsx](./src/components/Live2D/Live2DModel.jsx) - Live2D模型渲染组件
    - [LoadingDots.jsx](./src/components/LoadingDots.jsx) - 加载动画组件
    - [Sidebar.jsx](./src/components/Sidebar.jsx)  - 侧边栏组件
  - `pages/` - 页面组件
    - [MainPage.jsx](./src/pages/MainPage.jsx)   - 主页组件
  - [App.css](./src/App.css) - 主应用样式
  - [App.jsx](./src/App.jsx) - 主应用组件
  - [index.css](./src/index.css) - 全局样式
  - [main.jsx](./src/main.jsx) - 应用入口文件
- [index.html](./index.html) - HTML模板文件，浏览器加载的主页面
- [package.json](./node_modules/@babel/core/package.json) - 项目依赖和脚本配置
- [vite.config.js](./vite.config.js) - Vite构建配置
- [README_frontend_cn.md](./README_frontend_cn.md) - 前端技术文档

典型的 React 应用入口结构：

- [main.jsx](./src/main.jsx)：应用启动点
- [App.jsx](./src/App.jsx)：根组件
- [MainPage.jsx](./src/pages/MainPage.jsx)：具体功能页面

视觉层级关系
```
.app (黑色背景, 相对定位)
  ↓
  .live2d-main (绝对定位, 覆盖整个.app)
    ↓
    .live2d-container (PIXI画布容器, z-index: 1)
    .subtitles (字幕区域, z-index: 1000)
  ↓
  其他组件 (MessageList, InputArea等)
```

## 主要功能

从 [App.jsx](./src/App.jsx) 文件可以看出，应用通过React Router管理路由，主要页面为 [MainPage](./src/pages/MainPage.jsx)，其中集成了Live2D模型展示、聊天交互等功能。前端主要实现以下功能：

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



# 主页面 MainPage.jsx
主页面 [MainPage.jsx](./src/pages/MainPage.jsx) 是应用的主要页面，负责展示Live2D模型和聊天交互功能。根据提供的代码，主页面通过 [Live2DController](./src/components/Live2D/Live2DController.jsx) 组件来控制Live2D模型：

## 1. 组件引入和引用

```javascript
import Live2DController from '../components/Live2D/Live2DController';
const live2dControllerRef = useRef(null);
```

- 使用 `import` 语句引入 [Live2DController](./src/components/Live2D/Live2DController.jsx) 组件
- 使用 [useRef](./node_modules/@types/react/index.d.ts#L2020-L2020) 创建 [live2dControllerRef](./src/pages/MainPage.jsx#L20-L20) 用于获取组件实例

## 2. 组件渲染

```jsx
<Live2DController ref={live2dControllerRef} />
```

在JSX中渲染 [Live2DController](./src/components/Live2D/Live2DController.jsx) 组件，并将 [live2dControllerRef](./src/pages/MainPage.jsx#L20-L20) 作为 [ref](./node_modules/@types/react/index.d.ts#L362-L362) 属性传递给组件。

## 3. 方法调用

主页面通过 `live2dControllerRef.current` 调用 [Live2DController](./src/components/Live2D/Live2DController.jsx) 组件暴露的方法：

### 1. 显示表情

```javascript
// 在 handleSendMessage 函数中
if (parsedData.expression && live2dControllerRef.current) {
  live2dControllerRef.current.showExpression(parsedData.expression);
}
```

### 2. 重置表情

```javascript
// 在 playSentences 函数结束后
if (live2dControllerRef.current) {
  live2dControllerRef.current.resetExpression();
}
```

## 4. 架构说明

[Live2DController](./src/components/Live2D/Live2DController.jsx) 组件作为中介层，封装了对 [Live2DModel](./src/components/Live2D/Live2DModel.jsx#L7-L153) 组件的调用，提供了更简洁的API接口：
- `showExpression(expression, active)` - 显示指定表情
- `setTracking(enabled)` - 启用/禁用模型跟踪功能
- `resetExpression()` - 重置模型表情

这种设计模式提供了更好的封装性和可维护性，使主页面无需直接与底层的Live2DModel组件交互。

