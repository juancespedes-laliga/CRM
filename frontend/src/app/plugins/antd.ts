import type { App } from 'vue'
import Antd from 'ant-design-vue'
// El reset de Ant Design se importa en app/styles/style.css, dentro de la capa base de Tailwind.

export function installAntd(app: App) {
  app.use(Antd)
}
