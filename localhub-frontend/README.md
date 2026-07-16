# LocalHub Frontend (Vue 3 + Vite)

기존 `index_db2.html`(CDN Vue 3 단일 파일)을 Vite 기반 Vue 3 프로젝트로 변환한 결과물입니다.
`kakaomap.html`은 지도 SDK(전역 side-effect)와 iframe 통신(`postMessage`) 구조를 그대로 유지하기 위해
`public/kakaomap.html` 정적 파일로 두고, 빌드 시점에 API 주소/카카오 키만 주입합니다.

## 로컬 개발

```bash
npm install
npm run dev
```

`.env.development` 에 로컬 백엔드 주소(`http://localhost:8000`)와 카카오 JS 키가 이미 설정되어 있습니다.
카카오 키만 본인 키로 바꿔주세요.

## 빌드

```bash
npm run build
```

`vite build` 후 `scripts/inject-env.mjs`가 실행되어 `dist/kakaomap.html` 안의
`%%RUNTIME_API_BASE_URL%%`, `%%RUNTIME_KAKAO_JS_KEY%%` 플레이스홀더를
`VITE_API_BASE_URL`, `VITE_KAKAO_APP_KEY` 환경변수 값으로 치환합니다.
(`index_db2.html`에서 옮겨온 `App.vue` 쪽은 `import.meta.env.VITE_API_BASE_URL`을 Vite가 빌드 시점에 직접 치환합니다.)

## Netlify 배포

1. 이 폴더를 GitHub 저장소로 푸시
2. Netlify에서 "Add new site" → 해당 저장소 선택 (Build command/Publish directory는 `netlify.toml`에 이미 설정됨)
3. Site settings → Environment variables 에 아래 값 등록
   - `VITE_API_BASE_URL` = Render에 배포한 백엔드 주소 (예: `https://localhub-api.onrender.com`, 끝에 `/` 없이)
   - `VITE_KAKAO_APP_KEY` = 카카오 개발자 콘솔의 JavaScript 키
4. **중요**: 카카오 개발자 콘솔 → 내 애플리케이션 → 플랫폼 → Web 플랫폼에 Netlify 배포 도메인을 등록해야 지도가 정상 작동합니다.
5. Deploy 실행

## 남은 작업 (원본 프로젝트에 있었지만 이번에 전달받지 못한 파일)

`index_db2.html`이 참조하던 아래 커스텀 CSS 파일들은 이번 변환 대상 파일 목록(`index_db2.html`, `kakaomap.html`, `main.py`)에
포함되어 있지 않아 내용을 옮기지 못했습니다. 원본 프로젝트의 `css/` 폴더에서 복사해 오세요.

- `layout.css`, `navi.css`, `headerglass.css`, `cardlift.css`, `homehero.css`,
  `list.css`, `background.css`, `fadeshift.css`, `glasscard.css`, `body.css`

방법: 위 파일들을 `src/assets/legacy-css/` 에 넣고, `src/style.css` 상단 주석에 적힌 대로
`src/main.js`에서 `import`해주세요. (Tailwind 유틸리티 클래스 자체는 이미 `src/style.css`에서
`@tailwind` 지시어로 정상 동작합니다. 위 파일들은 Tailwind 위에 얹힌 커스텀 스타일입니다.)

`img/` 폴더의 이미지 파일들도 마찬가지로 원본에서 복사해 `public/img/`에 넣으면
기존과 동일한 `/img/...` 경로로 그대로 서빙됩니다.
