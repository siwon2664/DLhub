// Netlify(정적 호스팅)는 kakaomap.html을 순수 정적 파일로 그대로 서빙하므로,
// 원래 FastAPI(Jinja2)가 서버에서 넣어주던 카카오맵 JS 키와 API 서버 주소를
// 빌드 시점에 이 스크립트로 치환해 넣어준다.
// (index_db2.html → App.vue 쪽은 import.meta.env.VITE_API_BASE_URL을 그대로 쓰므로 대상이 아님)
import { readFileSync, writeFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const target = path.join(__dirname, '..', 'dist', 'kakaomap.html')

const apiBaseUrl = process.env.VITE_API_BASE_URL || 'http://localhost:8000'
const kakaoKey = process.env.VITE_KAKAO_APP_KEY || ''

if (!kakaoKey) {
  console.warn('[inject-env] 경고: VITE_KAKAO_APP_KEY 환경변수가 설정되지 않았습니다. 지도가 로드되지 않습니다.')
}

let html = readFileSync(target, 'utf-8')
html = html.split('%%RUNTIME_API_BASE_URL%%').join(apiBaseUrl)
html = html.split('%%RUNTIME_KAKAO_JS_KEY%%').join(kakaoKey)
writeFileSync(target, html)

console.log(`[inject-env] kakaomap.html 에 API_BASE_URL=${apiBaseUrl} 주입 완료`)
