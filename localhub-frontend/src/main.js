import { createApp } from 'vue'
import './style.css'

// 원본 프로젝트(css/ 폴더)의 커스텀 스타일. index_db2.html에서 로드하던 순서와 동일하게 유지.
// (hwamyeon.css는 원본 index_db2.html에서도 주석 처리되어 있어 실제로는 사용되지 않았음)
import './assets/legacy-css/layout.css'
import './assets/legacy-css/navi.css'
import './assets/legacy-css/headerglass.css'
import './assets/legacy-css/cardlift.css'
import './assets/legacy-css/homehero.css'
import './assets/legacy-css/list.css'
import './assets/legacy-css/background.css'
import './assets/legacy-css/fadeshift.css'
import './assets/legacy-css/glasscard.css'
import './assets/legacy-css/body.css'

import App from './App.vue'

createApp(App).mount('#app')
