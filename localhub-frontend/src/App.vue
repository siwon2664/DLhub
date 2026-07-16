<template>
    <div id="localhub-app" class="flex flex-col h-full w-full bg-white relative">
        
        <!-- [1. 상단 헤더 영역] -->
        <header class="flex justify-between items-center p-4 border-b border-gray-200 shrink-0 bg-white z-10">
            <div class="flex items-center gap-6">
                <!-- 로고 -->
                <h1 @click="changeView('home')" class="text-2xl font-bold text-blue-500 cursor-pointer flex items-center gap-2">
                    <i class="fas fa-map-marked-alt text-xl"></i>
                    <span>DLHub</span>
                </h1>
                
                <!-- 데스크톱 글로벌 네비게이션 (md 이상에서 표시) -->
                <nav class="hidden md:flex gap-4 font-medium text-gray-600">
                    <button @click="changeView('home')" :class="{'text-blue-500': currentView === 'home'}" class="hover:text-blue-500 px-2 py-1 transition-colors">홈</button>
                    <button @click="changeView('map')" :class="{'text-blue-500': currentView === 'map'}" class="hover:text-blue-500 px-2 py-1 transition-colors">지역 지도</button>
                    <button @click="changeView('board-list')" :class="{'text-blue-500': currentView.includes('board')}" class="hover:text-blue-500 px-2 py-1 transition-colors">커뮤니티</button>
                </nav>
            </div>

            <div class="flex items-center gap-4">
                <!-- 날씨 정보 위젯 -->
                <button
                    type="button"
                    @click="loadWeather"
                    :disabled="weatherLoading"
                    class="flex items-center gap-2 bg-blue-50 px-3 py-1.5 rounded-full text-xs md:text-sm text-blue-800 disabled:opacity-60"
                    :title="weatherError || '클릭하여 날씨 새로고침'"
                    aria-label="대전 현재 날씨 새로고침"
                >
                    <i :class="[weatherIcon, weatherIconColor, { 'fa-spin': weatherLoading }]" class="fas"></i>
                    <span>{{ weatherText }}</span>
                </button>
                <!-- 실시간 접속자 수 -->
                <div v-if="onlineCount !== null" class="flex items-center gap-1.5 px-1" aria-live="polite">
                    <span class="relative flex h-2 w-2">
                        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                        <span class="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                    </span>
                    <span class="text-xs md:text-sm text-gray-500">{{ onlineCount }}명 접속중</span>
                </div>
                <!-- 검색 아이콘 -->
                <button @click="changeView('search')" class="p-2 text-gray-500 hover:text-black" aria-label="통합 검색">
                    <i class="fas fa-search text-lg"></i>
                </button>
            </div>
        </header>

        <!-- [2. 메인 콘텐츠 영역 (동적 라우팅 렌더링)] -->
        <!-- 모바일 하단 네비게이션 바 높이를 고려해 pb-16 추가 (md 이상에서는 pb-0) -->
        <main class="flex-1 overflow-y-auto relative pb-16 md:pb-0">
            <transition name="fade" mode="out-in">
                
                <!-- 뷰 A: 홈 화면 (와이어프레임 메인) -->
                <div v-if="currentView === 'home'" key="home" class="p-4 md:p-6">
                    <!-- 히어로 배너 -->
                    <div class="home-hero bg-blue-50 py-8 md:py-12 text-center rounded-lg mb-6 md:mb-8 px-4">
                        <h2 class="text-2xl md:text-3xl font-bold text-blue-500 mb-2">오늘의 대전을 더 가깝게</h2>
                        <p class="text-sm md:text-base text-gray-600">장소, 이야기, 동네 소식을 한곳에서 확인하세요.</p>
                    </div>

                    <!-- 카테고리 -->
                    <div class="mb-8 md:mb-10">
                        <h3 class="text-base md:text-lg font-bold mb-4">무엇을 찾고 있나요?</h3>
                        <div class="grid grid-cols-3 gap-3 md:gap-4">
                            <button @click="openMapCategory('12')" class="border border-gray-300 p-4 md:p-6 flex flex-col items-center justify-center hover:bg-gray-50 transition rounded-lg">
                                <div class="w-12 h-10 md:w-16 md:h-12 bg-gray-100 mb-2 flex items-center justify-center rounded"><i class="fas fa-map-marked-alt text-gray-400"></i></div>
                                <span class="font-bold text-xs md:text-sm">관광지</span>
                            </button>
                            <button @click="openMapCategory('39')" class="border border-gray-300 p-4 md:p-6 flex flex-col items-center justify-center hover:bg-gray-50 transition rounded-lg">
                                <div class="w-12 h-10 md:w-16 md:h-12 bg-gray-100 mb-2 flex items-center justify-center rounded"><i class="fas fa-utensils text-gray-400"></i></div>
                                <span class="font-bold text-xs md:text-sm">맛집</span>
                            </button>
                            <button @click="openMapCategory('15')" class="border border-gray-300 p-4 md:p-6 flex flex-col items-center justify-center hover:bg-gray-50 transition rounded-lg">
                                <div class="w-12 h-10 md:w-16 md:h-12 bg-gray-100 mb-2 flex items-center justify-center rounded"><i class="fas fa-calendar-alt text-gray-400"></i></div>
                                <span class="font-bold text-xs md:text-sm">축제·행사</span>
                            </button>
                        </div>
                    </div>

                    <!-- 현재 인기게시물 (조회수 TOP 3) -->
                    <div class="mb-8 md:mb-10">
                        <div class="flex justify-between items-end mb-4">
                            <h3 class="text-base md:text-lg font-bold">현재 인기게시물</h3>
                            <button @click="changeView('board-list')" class="text-xs md:text-sm text-gray-500 hover:underline">더보기 &gt;</button>
                        </div>
                        <div v-if="popularPostsLoading" class="py-6 text-center text-xs text-gray-400"><i class="fas fa-spinner fa-spin mr-2"></i>인기 게시물을 불러오는 중입니다.</div>
                        <ul v-else-if="popularPosts.length" class="border-t border-gray-200">
                            <li v-for="(post, index) in popularPosts" :key="post.id" @click="openPost(post.id)" class="py-3 border-b border-gray-100 flex items-center gap-3 hover:bg-gray-50 cursor-pointer text-xs md:text-sm">
                                <span class="shrink-0 w-5 h-5 flex items-center justify-center rounded-full bg-gray-100 text-gray-500 font-bold text-[11px]">{{ index + 1 }}</span>
                                <span class="truncate flex-1">{{ post.title }}</span>
                                <span class="text-gray-400 shrink-0"><i class="far fa-eye mr-1"></i>{{ post.views || 0 }}</span>
                            </li>
                        </ul>
                        <div v-else class="py-6 text-center text-xs text-gray-400">아직 게시글이 없습니다.</div>
                    </div>

                    <!-- 지금 올라온 이야기 -->
                    <div class="mb-8 md:mb-10">
                        <div class="flex justify-between items-end mb-4">
                            <h3 class="text-base md:text-lg font-bold">지금 올라온 이야기</h3>
                            <button @click="changeView('board-list')" class="text-xs md:text-sm text-gray-500 hover:underline">더보기 &gt;</button>
                        </div>
                        <ul class="border-t border-gray-200">
                            <li v-for="post in recentPosts" :key="post.id" @click="openPost(post.id)" class="py-3 border-b border-gray-100 flex justify-between items-center hover:bg-gray-50 cursor-pointer text-xs md:text-sm">
                                <span class="truncate pr-4">{{ post.title }}</span>
                                <span class="text-gray-400 shrink-0">{{ formatDate(post.created_at) }}</span>
                            </li>
                        </ul>
                    </div>

                    <!-- Upcoming Event · Custom Calendar (홈 최하단) -->
                    <section class="grid grid-cols-1 lg:grid-cols-[minmax(0,0.82fr)_minmax(0,1.18fr)] gap-4 md:gap-6">
                        <!-- 게시글 해시태그 기반 핫 플레이스 -->
                        <div class="order-1 lg:order-2 border border-orange-100 rounded-2xl bg-gradient-to-br from-white to-orange-50/40 p-4 md:p-5 shadow-sm">
                            <div class="flex items-center justify-between mb-4">
                                <div>
                                    <p class="text-[11px] font-bold tracking-wider text-orange-500 mb-1">HOT PLACE</p>
                                    <h3 class="text-base md:text-lg font-bold">핫 플레이스</h3>
                                </div>
                                <span v-if="hotPlace.regions.length" class="text-[11px] bg-orange-100 text-orange-700 px-2 py-1 rounded-full">해시태그 TOP {{ hotPlace.regions.length }}</span>
                            </div>
                            <div v-if="hotPlaceLoading && !hotPlace.regions.length" class="py-12 text-center text-sm text-gray-400"><i class="fas fa-spinner fa-spin mr-2"></i>핫 플레이스를 분석하는 중입니다.</div>
                            <div v-else-if="hotPlaceError" class="py-12 text-center text-sm text-red-500">{{ hotPlaceError }}</div>
                            <div v-else-if="!hotPlace.regions.length" class="py-12 text-center text-sm text-gray-400">동네 해시태그가 쌓이면 핫 플레이스를 알려드립니다.</div>
                            <div v-else class="space-y-4">
                                <div class="flex flex-wrap gap-2">
                                    <button v-for="region in hotPlace.regions" :key="region.neighborhood" @click="selectHotPlaceRegion(region.neighborhood)" class="text-xs font-semibold px-3 py-1.5 rounded-full border transition" :class="hotPlace.selectedRegion === region.neighborhood ? 'bg-orange-100 border-orange-700 text-orange-700 shadow-sm hover:bg-orange-200' : 'bg-orange-50 border-orange-400 text-orange-800 hover:bg-orange-100 hover:border-orange-600'">#{{ region.neighborhood }} <span class="opacity-90">{{ region.mention_count }}</span></button>
                                    <i v-if="hotPlaceLoading" class="fas fa-spinner fa-spin self-center text-orange-600 text-xs" aria-label="장소 목록을 불러오는 중"></i>
                                </div>
                                <p v-if="!hotPlace.selectedRegion" class="py-8 text-center text-sm text-gray-400">해시태그를 선택하면 해당 지역의 장소를 보여드립니다.</p>
                                <transition v-else name="hot-place-slide" mode="out-in">
                                <div :key="hotPlace.selectedRegion">
                                    <template v-for="(places, category) in hotPlace.items" :key="category">
                                        <div v-if="places.length">
                                            <p class="text-xs font-bold text-orange-700 mb-2"><i :class="category === '맛집' ? 'fas fa-utensils' : 'fas fa-map-location-dot'" class="mr-1"></i>{{ category }}</p>
                                            <div class="space-y-2"><button v-for="place in places" :key="place.contentid" @click="openHotPlaceOnMap(place)" class="w-full text-left border border-orange-100/80 bg-white rounded-xl px-3 py-2.5 hover:border-orange-300 hover:bg-orange-50 transition flex items-center gap-3"><div class="poi-thumb shrink-0 w-12 h-12 rounded-lg bg-gray-200 overflow-hidden"><img v-if="place.firstimage" :src="place.firstimage" class="w-full h-full object-cover" onerror="this.style.display='none'"></div><div class="min-w-0 flex-1"><p class="font-bold text-sm text-gray-800 truncate">{{ place.title }}</p><p class="text-[11px] text-gray-500 mt-1 truncate"><i class="fas fa-location-dot mr-1 text-orange-400"></i>{{ place.address }}</p></div></button></div>
                                        </div>
                                    </template>
                                </div>
                                </transition>
                            </div>
                        </div>

                        <div class="order-2 lg:order-1 self-start border border-orange-100 rounded-2xl bg-gradient-to-br from-white to-orange-50/50 p-3.5 md:p-4 shadow-sm">
                            <div class="flex items-center justify-between gap-3" :class="calendarExpanded ? 'mb-3' : ''">
                                <div>
                                    <p class="text-[10px] font-bold tracking-wider text-orange-500 mb-0.5">CALENDAR</p>
                                    <h3 class="text-sm md:text-base font-bold text-slate-800">월별 일정</h3>
                                </div>
                                <div class="flex items-center gap-1.5">
                                    <button type="button" @click="openCalendarModal" aria-label="큰 캘린더 열기" class="w-8 h-8 rounded-full bg-orange-50 text-orange-500 flex items-center justify-center hover:bg-orange-100 transition">
                                        <i class="far fa-calendar-alt text-sm"></i>
                                    </button>
                                    <button type="button" @click="toggleHomeCalendar" :aria-expanded="calendarExpanded" :aria-label="calendarExpanded ? '캘린더 접기' : '캘린더 펼치기'" class="h-8 px-2.5 rounded-full border border-orange-100 bg-white text-[11px] font-medium text-orange-600 hover:bg-orange-50 transition">
                                        <span>{{ calendarExpanded ? '접기' : '펼치기' }}</span>
                                        <i :class="calendarExpanded ? 'fa-chevron-up' : 'fa-chevron-down'" class="fas ml-1"></i>
                                    </button>
                                </div>
                            </div>
                            <transition name="calendar-collapse">
                                <div v-show="calendarExpanded" class="localhub-calendar-shell overflow-hidden">
                                    <div class="flex items-center justify-between mb-3">
                                        <button type="button" @click="moveCalendarMonth(-1)" class="calendar-nav-button" aria-label="이전 달"><i class="fas fa-chevron-left text-xs"></i></button>
                                        <button type="button" @click="goCalendarToday" class="text-base font-extrabold tracking-[-0.04em] text-slate-800 hover:text-orange-600">{{ calendarTitle }}</button>
                                        <button type="button" @click="moveCalendarMonth(1)" class="calendar-nav-button" aria-label="다음 달"><i class="fas fa-chevron-right text-xs"></i></button>
                                    </div>
                                    <div class="calendar-grid">
                                        <div v-for="weekday in calendarWeekdays" :key="weekday" class="calendar-weekday">{{ weekday }}</div>
                                        <button v-for="day in calendarDays" :key="day.dateKey" type="button" @click="selectCalendarDay(day)" class="calendar-day" :class="day.classes">
                                            <span class="calendar-day-number">{{ day.day }}</span>
                                            <div v-if="day.events.length" class="calendar-event-preview" @click.stop="openEventOnMap(day.events[0])"><span>{{ day.events[0].title }}</span></div>
                                            <p v-if="day.events.length > 1" class="calendar-event-count">+{{ day.events.length - 1 }}개</p>
                                        </button>
                                    </div>

                                    <!-- 선택한 날짜의 행사 사진 + 정보 -->
                                    <div class="mt-3 pt-3 border-t border-orange-100">
                                        <p class="text-[11px] font-bold text-orange-500 mb-2">{{ selectedCalendarDateLabel }} 일정</p>
                                        <div v-if="selectedCalendarEvents.length" class="flex flex-col gap-2 max-h-56 overflow-y-auto pr-1">
                                            <button
                                                v-for="event in selectedCalendarEvents"
                                                :key="`home-selected-${event.contentid || event.title}`"
                                                type="button"
                                                @click="openEventOnMap(event)"
                                                class="flex items-center gap-3 text-left border border-orange-100 rounded-lg p-2 hover:bg-orange-50 transition"
                                            >
                                                <img
                                                    v-if="event.firstimage"
                                                    :src="event.firstimage"
                                                    class="w-14 h-14 rounded-md object-cover shrink-0"
                                                    onerror="this.style.display='none'"
                                                >
                                                <div v-else class="w-14 h-14 rounded-md bg-orange-100 flex items-center justify-center text-orange-300 shrink-0">
                                                    <i class="fas fa-image"></i>
                                                </div>
                                                <div class="min-w-0 flex-1">
                                                    <p class="text-sm font-bold text-gray-800 truncate">{{ event.title }}</p>
                                                    <p class="text-[11px] text-gray-500 mt-0.5 truncate"><i class="fas fa-location-dot mr-1 text-orange-400"></i>{{ event.location }}</p>
                                                    <p class="text-[11px] text-gray-400 mt-0.5">{{ event.period }}</p>
                                                </div>
                                            </button>
                                        </div>
                                        <p v-else class="text-[11px] text-gray-400 text-center py-4">선택한 날짜에 예정된 행사가 없습니다.</p>
                                    </div>
                                </div>
                            </transition>
                        </div>
                    </section>

                    <!-- 월간 캘린더 모달 -->
                    <div v-if="calendarModalOpen" class="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4" @click.self="closeCalendarModal">
                        <div class="w-full max-w-5xl max-h-[90vh] overflow-y-auto bg-white rounded-2xl shadow-2xl p-5 md:p-6">
                            <div class="flex items-center justify-between mb-5">
                                <div>
                                    <p class="text-[11px] font-bold tracking-wider text-orange-500">EVENT CALENDAR</p>
                                    <h3 class="text-lg font-bold mt-1">월별 이벤트 캘린더</h3>
                                </div>
                                <button type="button" @click="closeCalendarModal" class="w-9 h-9 rounded-full border border-gray-200 hover:bg-gray-50" aria-label="캘린더 닫기"><i class="fas fa-times"></i></button>
                            </div>
                            <div class="localhub-calendar-shell">
                                <div class="flex items-center justify-between mb-4">
                                    <button type="button" @click="moveCalendarMonth(-1)" class="calendar-nav-button" aria-label="이전 달"><i class="fas fa-chevron-left text-xs"></i></button>
                                    <div class="text-center"><button type="button" @click="goCalendarToday" class="text-xl font-extrabold tracking-[-0.04em] text-slate-900 hover:text-orange-600">{{ calendarTitle }}</button><p class="text-[11px] text-slate-400 mt-1">날짜를 선택하면 해당 일정이 표시됩니다.</p></div>
                                    <button type="button" @click="moveCalendarMonth(1)" class="calendar-nav-button" aria-label="다음 달"><i class="fas fa-chevron-right text-xs"></i></button>
                                </div>
                                <div class="calendar-grid calendar-modal-grid">
                                    <div v-for="weekday in calendarWeekdays" :key="weekday" class="calendar-weekday">{{ weekday }}</div>
                                    <button v-for="day in calendarDays" :key="`modal-${day.dateKey}`" type="button" @click="selectCalendarDay(day)" class="calendar-day" :class="day.classes">
                                        <span class="calendar-day-number">{{ day.day }}</span>
                                        <div v-for="event in day.events.slice(0, 2)" :key="event.contentid || event.title" class="calendar-event-preview" @click.stop="openEventOnMap(event)"><span>{{ event.title }}</span></div>
                                        <p v-if="day.events.length > 2" class="calendar-event-count">+{{ day.events.length - 2 }}개 일정</p>
                                    </button>
                                </div>
                                <div v-if="selectedCalendarEvents.length" class="mt-5 border border-orange-100 rounded-xl bg-orange-50/40 p-4">
                                    <p class="text-xs font-bold text-orange-600 mb-3">{{ selectedCalendarDateLabel }} 일정</p>
                                    <button v-for="event in selectedCalendarEvents" :key="`selected-${event.contentid || event.title}`" @click="openEventOnMap(event)" class="w-full flex items-center justify-between gap-4 py-2.5 border-b last:border-0 border-orange-100 text-left">
                                        <span class="text-sm font-bold text-slate-800 truncate">{{ event.title }}</span><span class="text-xs text-orange-600 shrink-0">지도 보기 <i class="fas fa-chevron-right ml-1"></i></span>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 뷰 B: 통합 검색 화면 -->
                <div v-else-if="currentView === 'search'" key="search" class="p-4 md:p-8 max-w-5xl mx-auto w-full">
                    <div class="mb-6 md:mb-8">
                        <p class="text-xs font-bold text-orange-600 mb-2">SEARCH</p>
                        <h2 class="text-2xl md:text-3xl font-bold tracking-tight">대전 통합 검색</h2>
                        <p class="text-sm text-gray-500 mt-2">장소와 커뮤니티 게시글을 한 번에 검색하세요.</p>
                        <p v-if="usingMockData" class="inline-flex items-center gap-2 mt-3 px-3 py-1.5 rounded-full bg-amber-50 text-amber-700 text-xs">
                            <i class="fas fa-flask"></i> 서버 미연결 테스트 모드 · 샘플 데이터 사용 중
                        </p>
                    </div>

                    <section class="border border-gray-200 rounded-2xl bg-white p-5 md:p-6">
                        <div class="flex items-start justify-between gap-4 mb-5">
                            <div>
                                <h3 class="text-lg md:text-xl font-bold">무엇을 찾고 있나요?</h3>
                                <p class="text-xs md:text-sm text-gray-500 mt-1">장소명, 주소, 게시글 제목·내용·태그를 함께 검색합니다.</p>
                            </div>
                            <i class="fas fa-magnifying-glass text-xl text-orange-500 mt-1"></i>
                        </div>

                        <div class="relative">
                            <i class="fas fa-search absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 text-sm"></i>
                            <input
                                v-model="unifiedSearchKeyword"
                                @input="handleUnifiedAutocomplete"
                                @focus="unifiedAutocompleteOpen = true"
                                @keydown.down.prevent="moveUnifiedSuggestion(1)"
                                @keydown.up.prevent="moveUnifiedSuggestion(-1)"
                                @keydown.enter.prevent="submitUnifiedSearch"
                                @keydown.esc="unifiedAutocompleteOpen = false"
                                type="search"
                                autocomplete="off"
                                placeholder="예: 성심당, 유성구 행사, 둔산동 주차"
                                class="w-full border border-gray-300 rounded-xl pl-10 pr-10 py-3.5 text-sm focus:outline-none focus:border-gray-800"
                            >
                            <i v-if="searchLoading" class="fas fa-spinner fa-spin absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 text-sm"></i>

                            <div v-if="unifiedAutocompleteOpen && unifiedSearchKeyword.trim()" class="absolute z-30 left-0 right-0 mt-2 bg-white border border-gray-200 rounded-xl shadow-xl overflow-hidden max-h-[430px] overflow-y-auto">
                                <div v-if="unifiedMapSuggestions.length">
                                    <div class="px-4 py-2 text-[11px] font-bold tracking-wider text-orange-600 bg-orange-50/60">지도</div>
                                    <button
                                        v-for="(place, index) in unifiedMapSuggestions"
                                        :key="`place-${place.name}`"
                                        @mousedown.prevent="selectUnifiedSuggestion({ type: 'place', item: place })"
                                        :class="index === activeUnifiedSuggestion ? 'bg-orange-50' : 'bg-white'"
                                        class="w-full text-left px-4 py-3 border-b last:border-b-0 border-gray-100 hover:bg-orange-50 transition"
                                    >
                                        <div class="flex items-center justify-between gap-4">
                                            <div class="min-w-0">
                                                <p class="font-bold text-sm truncate">{{ place.name }}</p>
                                                <p class="text-xs text-gray-500 truncate mt-1">{{ place.address }}</p>
                                            </div>
                                            <span class="text-[11px] text-orange-600 shrink-0">{{ place.tags[0] }}</span>
                                        </div>
                                    </button>
                                </div>

                                <div v-if="communitySuggestions.length">
                                    <div class="px-4 py-2 text-[11px] font-bold tracking-wider text-orange-600 bg-orange-50/60">커뮤니티</div>
                                    <button
                                        v-for="(post, index) in communitySuggestions"
                                        :key="`post-${post.id}`"
                                        @mousedown.prevent="selectUnifiedSuggestion({ type: 'post', item: post })"
                                        :class="unifiedMapSuggestions.length + index === activeUnifiedSuggestion ? 'bg-orange-50' : 'bg-white'"
                                        class="w-full text-left px-4 py-3 border-b last:border-b-0 border-gray-100 hover:bg-orange-50 transition"
                                    >
                                        <p class="font-bold text-sm truncate">{{ post.title }}</p>
                                        <p class="text-xs text-gray-500 truncate mt-1">{{ post.content }}</p>
                                        <div v-if="post.tags && post.tags.length" class="flex gap-2 mt-2">
                                            <span v-for="tag in post.tags.slice(0, 3)" :key="tag" class="text-[11px] text-orange-600">#{{ tag }}</span>
                                        </div>
                                    </button>
                                </div>

                                <div v-if="!searchLoading && !unifiedMapSuggestions.length && !communitySuggestions.length" class="px-4 py-8 text-sm text-gray-400 text-center">
                                    일치하는 장소나 게시글이 없습니다.
                                </div>
                            </div>
                        </div>
                        <div v-if="unifiedSearchSubmitted" class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-5">
                            <section class="border border-orange-100 rounded-xl overflow-hidden"><h3 class="px-4 py-2.5 bg-orange-50 text-sm font-bold text-orange-700">지도 검색 결과</h3><button v-for="place in unifiedPlaceResults" :key="place.contentid" @click="openPlaceOnMap(place)" class="w-full text-left px-4 py-3 border-t hover:bg-orange-50"><p class="font-bold text-sm">{{ place.name }}</p><p class="text-xs text-gray-500 mt-1 truncate">{{ place.address }}</p></button><p v-if="!unifiedPlaceResults.length" class="p-5 text-center text-xs text-gray-400">지도 검색 결과가 없습니다.</p></section>
                            <section class="border border-blue-100 rounded-xl overflow-hidden"><h3 class="px-4 py-2.5 bg-blue-50 text-sm font-bold text-blue-700">커뮤니티 검색 결과</h3><button v-for="post in communitySearchResults" :key="post.id" @click="openPost(post.id)" class="w-full text-left px-4 py-3 border-t hover:bg-blue-50"><p class="font-bold text-sm truncate">{{ post.title }}</p><p class="text-xs text-gray-500 mt-1 truncate">{{ post.content }}</p></button><p v-if="!communitySearchResults.length" class="p-5 text-center text-xs text-gray-400">커뮤니티 검색 결과가 없습니다.</p></section>
                        </div>
                    </section>
                </div>

                <!-- 뷰 B: 지역 지도 화면 (좌측 리스트 + 우측 맵) -->
                <div v-else-if="currentView === 'map'" key="map" class="h-full flex flex-col md:flex-row">
                    <!-- 좌측 사이드 메뉴 (정보 리스트) -->
                    <div
                        :class="mapSearchPanelOpen ? 'h-[30vh]' : 'h-8'"
                        class="w-full md:w-80 md:h-full border-r border-gray-200 flex flex-col bg-white shrink-0 order-2 md:order-1 overflow-hidden transition-all duration-300"
                    >
                        <!-- 핸들: 이 영역을 누르면 검색창이 접히거나 펼쳐짐 (모바일 전용) -->
                        <button
                            type="button"
                            @click="mapSearchPanelOpen = !mapSearchPanelOpen"
                            class="shrink-0 w-full h-8 flex items-center justify-center gap-1 text-gray-400 hover:bg-gray-50 border-b border-gray-100 md:hidden"
                        >
                            <i :class="mapSearchPanelOpen ? 'fa-chevron-down' : 'fa-chevron-up'" class="fas text-[10px]"></i>
                            <span class="text-[11px]">{{ mapSearchPanelOpen ? '검색창 접기' : '검색창 펼치기' }}</span>
                        </button>
                        <div class="map-search-panel p-3 md:p-4 border-b relative">
                            <!-- 장소 검색 / 길찾기 모드 전환 탭 -->
                            <div class="flex gap-1 mb-2 bg-gray-100 rounded-lg p-0.5">
                                <button type="button" @click="setBusPlanMode(false)"
                                        :class="!busPlanMode ? 'bg-white shadow text-gray-800' : 'text-gray-400 hover:text-gray-600'"
                                        class="flex-1 text-xs font-bold py-1.5 rounded-md transition">🔍 장소 검색</button>
                                <button type="button" @click="setBusPlanMode(true)"
                                        :class="busPlanMode ? 'bg-white shadow text-gray-800' : 'text-gray-400 hover:text-gray-600'"
                                        class="flex-1 text-xs font-bold py-1.5 rounded-md transition">🚌 길찾기</button>
                            </div>
                            <div v-if="!busPlanMode" class="relative">
                                <i class="fas fa-search absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-xs"></i>
                                <input
                                    v-model="mapSearchKeyword"
                                    @input="handleMapAutocomplete"
                                                                        @keydown.down.prevent="moveMapSuggestion(1)"
                                    @keydown.up.prevent="moveMapSuggestion(-1)"
                                    @keydown.enter.prevent="selectActiveMapSuggestion"
                                    @keydown.esc="activeMapSuggestion = -1"
                                    type="search"
                                    autocomplete="off"
                                    placeholder="장소명 또는 주소 검색"
                                    class="map-search-input w-full border border-gray-300 pl-9 pr-9 py-2.5 rounded-lg text-sm focus:outline-none focus:border-blue-500"
                                >
                                <i v-if="mapSearchLoading" class="fas fa-spinner fa-spin absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 text-xs"></i>
                            </div>
                            <!-- 길찾기 모드: 출발지/도착지 입력 -->
                            <div v-else class="space-y-2">
                                <div class="relative">
                                    <span class="absolute left-3 top-[13px] w-2 h-2 rounded-full bg-green-500"></span>
                                    <input
                                        v-model.trim="busStart.keyword"
                                        @input="handleBusAutocomplete('start')"
                                        @focus="busStart.open = true; activeBusField = 'start'"
                                        @blur="busStart.open = false"
                                        @keydown.enter.prevent="requestBusPlan"
                                        type="search" autocomplete="off" placeholder="출발지 (장소명 또는 주소)"
                                        :class="activeBusField === 'start' ? 'border-blue-500 ring-1 ring-blue-200' : 'border-gray-300'"
                                        class="w-full border pl-8 pr-8 py-2 rounded-lg text-sm focus:outline-none focus:border-blue-500"
                                    >
                                    <i v-if="busStart.loading" class="fas fa-spinner fa-spin absolute right-3 top-[11px] text-gray-400 text-xs"></i>
                                    <div v-if="busStart.open && busStart.results.length" class="absolute z-20 left-0 right-0 top-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto">
                                        <button v-for="place in busStart.results" :key="'s' + place.contentid" type="button"
                                                @mousedown.prevent="selectBusPlace('start', place)"
                                                class="w-full text-left px-3 py-2 hover:bg-blue-50 border-b border-gray-50">
                                            <p class="text-xs font-bold text-gray-800 truncate">{{ place.name }}</p>
                                            <p class="text-[10px] text-gray-400 truncate">{{ place.address }}</p>
                                        </button>
                                    </div>
                                </div>
                                <div class="relative">
                                    <span class="absolute left-3 top-[13px] w-2 h-2 rounded-full bg-red-500"></span>
                                    <input
                                        v-model.trim="busEnd.keyword"
                                        @input="handleBusAutocomplete('end')"
                                        @focus="busEnd.open = true; activeBusField = 'end'"
                                        @blur="busEnd.open = false"
                                        @keydown.enter.prevent="requestBusPlan"
                                        type="search" autocomplete="off" placeholder="도착지 (장소명 또는 주소)"
                                        :class="activeBusField === 'end' ? 'border-blue-500 ring-1 ring-blue-200' : 'border-gray-300'"
                                        class="w-full border pl-8 pr-8 py-2 rounded-lg text-sm focus:outline-none focus:border-blue-500"
                                    >
                                    <i v-if="busEnd.loading" class="fas fa-spinner fa-spin absolute right-3 top-[11px] text-gray-400 text-xs"></i>
                                    <div v-if="busEnd.open && busEnd.results.length" class="absolute z-20 left-0 right-0 top-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto">
                                        <button v-for="place in busEnd.results" :key="'e' + place.contentid" type="button"
                                                @mousedown.prevent="selectBusPlace('end', place)"
                                                class="w-full text-left px-3 py-2 hover:bg-blue-50 border-b border-gray-50">
                                            <p class="text-xs font-bold text-gray-800 truncate">{{ place.name }}</p>
                                            <p class="text-[10px] text-gray-400 truncate">{{ place.address }}</p>
                                        </button>
                                    </div>
                                </div>
                                <div class="flex gap-2">
                                    <button type="button" @click="swapBusPoints" title="출발지/도착지 바꾸기"
                                            class="shrink-0 w-9 h-9 flex items-center justify-center border border-gray-300 rounded-lg text-gray-500 hover:bg-gray-50 transition">
                                        <i class="fas fa-exchange-alt rotate-90 text-xs"></i>
                                    </button>
                                    <button type="button" @click="requestBusPlan" :disabled="busPlanLoading"
                                            class="flex-1 h-9 bg-blue-500 text-white text-sm font-bold rounded-lg hover:bg-blue-600 disabled:opacity-50 transition">
                                        <i class="fas fa-route mr-1 text-xs"></i>길찾기
                                    </button>
                                </div>
                                <p class="text-[10px] text-gray-400 leading-relaxed">
                                    <i class="fas fa-map-pin mr-0.5"></i>
                                    입력칸을 클릭한 뒤 지도의 핀을 누르면 {{ activeBusField === 'start' ? '출발지' : '도착지' }}에 주소가 자동 입력됩니다.
                                </p>
                            </div>
                        </div>
                        <div class="flex-1 overflow-y-auto">
                            <!-- 길찾기 모드: 추천 버스 경로 목록 -->
                            <template v-if="busPlanMode">
                                <div v-if="busPlanLoading" class="p-8 text-center text-xs text-gray-400"><i class="fas fa-spinner fa-spin mr-2"></i>버스 경로를 찾는 중입니다.</div>
                                <div v-else-if="busPlanError" class="p-8 text-center text-xs text-red-400">{{ busPlanError }}</div>
                                <div v-else-if="busPlanMessage" class="p-8 text-center text-xs text-gray-400">{{ busPlanMessage }}</div>
                                <template v-else-if="busPlans.length">
                                    <div class="px-3 md:px-4 pt-3 pb-1 flex items-center justify-between">
                                        <span class="text-[11px] text-gray-400">추천 경로 (도보·승차거리 기준)</span>
                                        <button type="button" @click="clearBusPlans" class="text-[11px] text-gray-400 hover:text-red-500">지우기</button>
                                    </div>
                                    <button
                                        v-for="(plan, index) in busPlans"
                                        :key="index"
                                        type="button"
                                        @click="showBusPlanOnMap(plan, index)"
                                        :class="index === activeBusPlanIndex ? 'bg-blue-50 border-l-2 border-l-blue-500' : 'bg-white'"
                                        class="w-full text-left p-3 md:p-4 border-b border-gray-100 hover:bg-blue-50 transition"
                                    >
                                        <div class="flex items-center gap-1.5 flex-wrap">
                                            <span v-for="(leg, legIndex) in plan.legs" :key="legIndex" class="inline-flex items-center gap-1.5">
                                                <i v-if="legIndex > 0" class="fas fa-arrow-right text-[10px] text-gray-300"></i>
                                                <span class="inline-flex items-center gap-1 bg-blue-500 text-white text-[11px] font-bold px-2 py-0.5 rounded-full">
                                                    <i class="fas fa-bus text-[9px]"></i>{{ leg.route_no }}번
                                                </span>
                                            </span>
                                            <span class="text-[10px] font-semibold px-1.5 py-0.5 rounded"
                                                  :class="plan.type === 'direct' ? 'bg-green-50 text-green-600' : 'bg-amber-50 text-amber-600'">
                                                {{ plan.type === 'direct' ? '직행' : '환승 1회' }}
                                            </span>
                                        </div>
                                        <p class="text-[11px] text-gray-500 mt-1.5 leading-relaxed">
                                            도보 {{ formatWalkDistance(plan.walk_start_km) }} → {{ plan.legs[0].route_no }}번 {{ plan.legs[0].ride_stops }}개 정류장<template v-if="plan.legs.length > 1"> → 환승 도보 {{ formatWalkDistance(plan.transfer_walk_km) }} → {{ plan.legs[1].route_no }}번 {{ plan.legs[1].ride_stops }}개 정류장</template> → 도보 {{ formatWalkDistance(plan.walk_end_km) }}
                                        </p>
                                        <p class="text-[10px] text-gray-400 mt-0.5">총 승차거리 약 {{ plan.total_ride_km.toFixed(1) }}km</p>
                                    </button>
                                </template>
                                <div v-else class="p-8 text-center text-xs text-gray-400">출발지와 도착지를 입력하고<br>길찾기 버튼을 눌러주세요.</div>
                            </template>
                            <!-- 검색어가 없을 때: 게시글에서 많이 언급된 동네의 추천 장소(무작위 3곳) -->
                            <template v-else-if="!mapSearchKeyword.trim()">
                                <div v-if="hotRandomLoading" class="p-8 text-center text-xs text-gray-400"><i class="fas fa-spinner fa-spin mr-2"></i>추천 장소를 불러오는 중입니다.</div>
                                <template v-else-if="hotRandomPlaces.length">
                                    <div class="px-3 md:px-4 pt-3 pb-1 text-[11px] text-gray-400">게시글에서 많이 언급된 동네의 추천 장소</div>
                                    <button
                                        v-for="place in hotRandomPlaces"
                                        :key="place.contentid"
                                        type="button"
                                        @click="openHotPlaceOnMap(place)"
                                        class="w-full text-left p-3 md:p-4 border-b border-gray-100 hover:bg-orange-50 transition flex items-center gap-3"
                                    >
                                        <div class="poi-thumb shrink-0 w-12 h-12 rounded-md bg-gray-200 overflow-hidden">
                                            <img v-if="place.firstimage" :src="place.firstimage" class="w-full h-full object-cover" onerror="this.style.display='none'">
                                        </div>
                                        <div class="min-w-0 flex-1">
                                            <h4 class="font-bold text-sm md:text-base text-gray-800 flex items-center gap-1.5">
                                                {{ place.title }}
                                                <span class="hot-badge">HOT</span>
                                            </h4>
                                            <p class="text-[11px] md:text-xs text-gray-500 mt-1 truncate">{{ place.address }}</p>
                                        </div>
                                    </button>
                                </template>
                                <div v-else class="p-8 text-center text-xs text-gray-400">아직 추천할 만한 장소가 없습니다.</div>
                            </template>
                            <template v-else>
                                <button
                                    v-for="(place, index) in mapSearchResults"
                                    :key="place.contentid || place.name"
                                    type="button"
                                    @click="openPlaceOnMap(place)"
                                    :class="index === activeMapSuggestion ? 'bg-orange-50' : 'bg-white'"
                                    class="w-full text-left p-3 md:p-4 border-b border-gray-100 hover:bg-orange-50 transition flex items-center gap-3"
                                >
                                    <div class="shrink-0 w-12 h-12 rounded-md bg-gray-200 overflow-hidden">
                                        <img v-if="place.firstimage" :src="place.firstimage" class="w-full h-full object-cover" onerror="this.style.display='none'">
                                    </div>
                                    <div class="min-w-0 flex-1">
                                        <h4 class="font-bold text-sm md:text-base text-gray-800 truncate" v-html="highlightMapMatch(place.name)"></h4>
                                        <p class="text-[11px] md:text-xs text-gray-500 mt-1 truncate" v-html="highlightMapMatch(place.address)"></p>
                                    </div>
                                </button>
                                <div v-if="!mapSearchLoading && !mapSearchResults.length" class="p-8 text-center text-xs text-gray-400">검색 결과가 없습니다.</div>
                            </template>
                        </div>
                    </div>
                    <!-- 우측 지도 영역 : 카카오맵(kakaomap.html)을 iframe으로 삽입 -->
                    <div id="map" class="flex-1 bg-gray-200 relative h-full min-h-[40vh] order-1 md:order-2">
                        <iframe
                            ref="mapFrameEl"
                            :key="mapFrameKey"
                            :src="mapFrameSrc"
                            title="카카오맵"
                            class="w-full h-full border-0"
                            loading="lazy"
                        ></iframe>
                    </div>
                </div>

                <!-- 뷰 C: 커뮤니티 목록 화면 -->
                <div v-else-if="currentView === 'board-list'" key="board-list" class="p-4 md:p-6">
                    <div class="community-breadcrumb text-xs md:text-sm text-orange-500 mb-2">홈 &gt; 커뮤니티</div>
                    <div class="flex items-center justify-between mb-5">
                        <div>
                            <h2 class="text-xl md:text-2xl font-bold">동네 이야기</h2>
                            <p class="text-xs text-gray-500 mt-1">대전에서 발견한 정보를 가볍게 나눠보세요.</p>
                        </div>
                        <span class="text-xs bg-blue-50 text-blue-700 px-3 py-1 rounded-full">총 {{ pagination.total }}건</span>
                    </div>

                    <div class="flex flex-col sm:flex-row justify-between items-stretch sm:items-center gap-3 mb-6">
                        <form @submit.prevent="searchPosts" class="flex gap-2 flex-1">
                            <input v-model.trim="searchKeyword" type="text" placeholder="제목·내용 검색 또는 #해시태그 검색" class="flex-1 border p-2 text-xs md:text-sm rounded focus:outline-blue-500">
                            <button class="bg-gray-700 text-white px-4 py-2 text-xs md:text-sm rounded hover:bg-gray-800 transition">검색</button>
                        </form>
                        <select v-model.number="pagination.size" @change="changePageSize" aria-label="페이지당 게시글 수" class="border bg-white px-3 py-2 text-xs md:text-sm rounded focus:outline-blue-500">
                            <option :value="10">10개씩 보기</option>
                            <option :value="20">20개씩 보기</option>
                        </select>
                        <select v-model="postPeriod" @change="changePostFilters" aria-label="조회 기간" class="border bg-white px-3 py-2 text-xs md:text-sm rounded focus:outline-blue-500">
                            <option value="all">전체 기간</option>
                            <option value="day">최근 1일</option>
                            <option value="week">최근 1주</option>
                            <option value="month">최근 1개월</option>
                            <option value="3months">최근 3개월</option>
                            <option value="year">최근 1년</option>
                        </select>
                        <button @click="openWriteView" class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 text-xs md:text-sm flex items-center justify-center gap-1 rounded transition">
                            <i class="fas fa-plus"></i> 글쓰기
                        </button>
                    </div>

                    <div v-if="loading" class="py-16 text-center text-sm text-gray-500"><i class="fas fa-spinner fa-spin mr-2"></i>게시글을 불러오는 중입니다.</div>
                    <div v-else-if="errorMessage" class="p-4 bg-red-50 text-red-700 rounded text-sm">{{ errorMessage }}</div>
                    <div v-else class="border-t-2 border-gray-300 overflow-hidden rounded-b-lg">
                        <div class="flex bg-gray-100 font-bold text-center py-3 text-xs md:text-sm">
                            <button @click="togglePostSort('id')" class="w-12 md:w-16">번호 {{ postSortBy === 'id' ? (postSortOrder === 'desc' ? '↓' : '↑') : '' }}</button>
                            <button @click="togglePostSort('title')" class="flex-1 text-left px-3 md:px-4">제목 {{ postSortBy === 'title' ? (postSortOrder === 'desc' ? '↓' : '↑') : '' }}</button>
                            <button @click="togglePostSort('views')" class="hidden sm:block w-20">조회 {{ postSortBy === 'views' ? (postSortOrder === 'desc' ? '↓' : '↑') : '' }}</button>
                            <button @click="togglePostSort('likes')" class="hidden sm:block w-20">좋아요 {{ postSortBy === 'likes' ? (postSortOrder === 'desc' ? '↓' : '↑') : '' }}</button>
                            <button @click="togglePostSort('recent')" class="w-24 md:w-32">작성일 {{ postSortBy === 'recent' ? (postSortOrder === 'desc' ? '↓' : '↑') : '' }}</button>
                        </div>
                        <ul v-if="boardPosts.length">
                            <li v-for="post in boardPosts" :key="post.id" @click="openPost(post.id)" class="flex py-3 border-b text-xs md:text-sm items-center hover:bg-blue-50 cursor-pointer">
                                <div class="w-12 md:w-16 text-center text-gray-500">{{ post.id }}</div>
                                <div v-if="post.images && post.images.length" class="w-10 h-10 md:w-12 md:h-12 rounded overflow-hidden bg-gray-100 border shrink-0">
                                    <img :src="post.images[0].dataUrl" class="w-full h-full object-cover" :alt="post.images[0].name || '첨부 이미지 미리보기'">
                                </div>
                                <div class="flex-1 px-3 md:px-4 min-w-0">
                                    <div class="flex items-center gap-2 min-w-0">
                                        <!-- <i v-if="post.images && post.images.length" class="far fa-image text-blue-500 shrink-0" title="이미지 첨부"></i> -->
                                        <p class="font-medium truncate">{{ post.title }}</p>
                                    </div>
                                    <div v-if="post.tags && post.tags.length" class="flex gap-1 mt-1 overflow-hidden">
    <span v-for="tag in post.tags.slice(0, 3)" :key="tag" @click.stop="searchByTag(tag)" class="text-[10px] text-blue-600 cursor-pointer hover:underline">#{{ tag }}</span>
</div>
                                </div>
                                <div class="hidden sm:block w-20 text-center text-gray-400"><i class="far fa-eye mr-1"></i>{{ post.views || 0 }}</div>
                                <div class="hidden sm:block w-20 text-center text-gray-400"><i class="far fa-heart mr-1"></i>{{ post.likes || 0 }}</div>
                                <div class="w-24 md:w-32 text-center text-gray-400">{{ formatDate(post.created_at) }}</div>
                            </li>
                        </ul>
                        <div v-else class="py-16 text-center text-sm text-gray-400">등록된 게시글이 없습니다.</div>
                    </div>

                    <div class="flex flex-wrap justify-center items-center gap-1 md:gap-2 mt-6 md:mt-8" v-if="pagination.total_pages > 1">
                        <button @click="goToPage(1)" :disabled="pagination.page === 1" class="border px-3 py-1 text-xs md:text-sm rounded disabled:opacity-40">처음</button>
                        <button @click="goToPage(pagination.page - 1)" :disabled="pagination.page === 1" class="border px-3 py-1 text-xs md:text-sm rounded disabled:opacity-40">&lt;</button>
                        <button v-for="page in visiblePages" :key="page" @click="goToPage(page)" :class="page === pagination.page ? 'border-blue-500 text-blue-500 font-bold' : 'text-gray-600'" class="border px-3 py-1 text-xs md:text-sm rounded">{{ page }}</button>
                        <button @click="goToPage(pagination.page + 1)" :disabled="pagination.page === pagination.total_pages" class="border px-3 py-1 text-xs md:text-sm rounded disabled:opacity-40">&gt;</button>
                        <button @click="goToPage(pagination.total_pages)" :disabled="pagination.page === pagination.total_pages" class="border px-3 py-1 text-xs md:text-sm rounded disabled:opacity-40">마지막</button>
                        <form @submit.prevent="jumpToPage" class="flex items-center gap-1 ml-1">
                            <input v-model.number="pageJumpInput" type="number" min="1" :max="pagination.total_pages" aria-label="이동할 페이지 번호" class="w-14 border px-2 py-1 text-xs md:text-sm rounded">
                            <button class="border px-2 py-1 text-xs md:text-sm rounded hover:bg-gray-50">이동</button>
                        </form>
                    </div>
                </div>

                <!-- 뷰 D: 커뮤니티 상세 화면 -->
                <div v-else-if="currentView === 'board-detail'" key="board-detail" class="p-4 md:p-6">
                    <div class="text-xs md:text-sm text-gray-500 mb-4 flex items-center gap-1">
                        <button @click="changeView('home')" class="hover:text-blue-500 hover:underline transition-colors">홈</button>
                        <span>&gt;</span>
                        <button @click="changeView('board-list')" class="hover:text-blue-500 hover:underline transition-colors">커뮤니티</button>
                        <span>&gt;</span>
                        <span>상세</span>
                    </div>
                    <div v-if="loading" class="py-16 text-center text-gray-500"><i class="fas fa-spinner fa-spin mr-2"></i>불러오는 중입니다.</div>
                    <article v-else-if="selectedPost" class="border-t-2 border-gray-800">
                        <header class="py-5 border-b">
                            <span class="text-xs text-blue-600">{{ selectedPost.region }}</span>
                            <h2 class="text-xl md:text-2xl font-bold mt-1 break-words">{{ selectedPost.title }}</h2>
                            <div class="flex flex-wrap items-center gap-3 text-xs text-gray-400 mt-3">
                                <span>작성 {{ formatDateTime(selectedPost.created_at) }}</span>
                                <span>수정 {{ formatDateTime(selectedPost.updated_at) }}</span>
                                <span><i class="far fa-eye mr-1"></i>{{ selectedPost.views || 0 }}</span>
                                <span><i class="far fa-heart mr-1"></i>{{ selectedPost.likes || 0 }}</span>
                            </div>
                            <div v-if="selectedPost.tags && selectedPost.tags.length" class="flex flex-wrap gap-2 mt-3">
                                <span v-for="tag in selectedPost.tags" :key="tag" class="bg-blue-50 text-blue-700 px-2 py-1 rounded-full text-xs">#{{ tag }}</span>
                            </div>
                        </header>
                        <div class="min-h-52 py-6">
                            <div v-if="selectedPost.images && selectedPost.images.length" class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
                                <img v-for="(image, index) in selectedPost.images" :key="index" :src="image.dataUrl" :alt="image.name || `첨부 이미지 ${index + 1}`" class="w-full max-h-96 object-contain bg-gray-50 border rounded">
                            </div>
                            <div class="whitespace-pre-wrap break-words text-sm md:text-base leading-7">{{ selectedPost.content }}</div>
                        </div>
                        <div class="border-t pt-4 flex flex-wrap justify-between gap-2">
                            <button @click="changeView('board-list')" class="border px-4 py-2 rounded text-sm hover:bg-gray-50">목록</button>
                            <div class="flex flex-wrap gap-2">
                                <button @click="toggleLike" :class="isLiked(selectedPost.id) ? 'bg-rose-50 border-rose-500 text-rose-600' : 'border-gray-300 text-gray-600'" class="border px-4 py-2 rounded text-sm">
                                    <i :class="isLiked(selectedPost.id) ? 'fas fa-heart' : 'far fa-heart'" class="mr-1"></i>좋아요 {{ selectedPost.likes || 0 }}
                                </button>
                                <button @click="openEditView" class="border border-blue-500 text-blue-600 px-4 py-2 rounded text-sm hover:bg-blue-50">수정</button>
                                <button @click="deletePost" class="border border-red-500 text-red-600 px-4 py-2 rounded text-sm hover:bg-red-50">삭제</button>
                            </div>
                        </div>
                    </article>
                </div>

                <!-- 뷰 E: 커뮤니티 작성·수정 화면 -->
                <div v-else-if="currentView === 'board-write'" key="board-write" class="p-4 md:p-6">
                    <div class="text-xs md:text-sm text-gray-500 mb-3 md:mb-4">홈 &gt; 커뮤니티 &gt; {{ editingPostId ? '수정' : '글쓰기' }}</div>
                    <h2 class="text-lg md:text-xl font-bold mb-4 md:mb-6">게시글 {{ editingPostId ? '수정' : '작성' }}</h2>

                    <form @submit.prevent="submitPost" class="space-y-4">
                        <div>
                            <label class="block font-bold mb-1.5 text-xs md:text-sm">제목</label>
                            <input v-model.trim="postForm.title" maxlength="200" required type="text" class="w-full border p-2 rounded text-xs md:text-sm focus:outline-blue-500" placeholder="제목을 입력하세요">
                        </div>
                        <div>
                            <label class="block font-bold mb-1.5 text-xs md:text-sm">내용</label>
                            <textarea v-model.trim="postForm.content" maxlength="10000" required rows="10" class="w-full border p-2 rounded text-xs md:text-sm resize-y focus:outline-blue-500" placeholder="내용을 입력하세요"></textarea>
                        </div>
                        <div>
                            <label class="block font-bold mb-1.5 text-xs md:text-sm">태그</label>
                            <input v-model="postForm.tagsText" maxlength="200" type="text" class="w-full border p-2 rounded text-xs md:text-sm focus:outline-blue-500" placeholder="쉼표로 구분해 입력하세요. 예: 맛집, 둔산동, 추천">
                            <p class="text-[10px] text-gray-400 mt-1">최대 10개까지 저장되며 검색 대상에 포함됩니다.</p>
                        </div>
                        <div>
                            <label class="block font-bold mb-1.5 text-xs md:text-sm">이미지 첨부</label>
                            <!-- 이미지 업로드 지원 활성화 -->
                            <input ref="imageInput" @change="handleImageUpload" accept="image/*" multiple type="file" class="block w-full text-xs text-gray-500 file:mr-3 file:px-3 file:py-2 file:border-0 file:rounded file:bg-blue-50 file:text-blue-700 cursor-pointer">
                            <p class="text-[10px] text-gray-400 mt-1">최대 3장, 이미지당 2MB 이하. 백엔드 데이터베이스에 직접 저장됩니다.</p>
                            <div v-if="postForm.images.length" class="grid grid-cols-2 sm:grid-cols-3 gap-3 mt-3">
                                <div v-for="(image, index) in postForm.images" :key="index" class="relative border rounded overflow-hidden bg-gray-50">
                                    <img :src="image.dataUrl" :alt="image.name" class="w-full h-28 object-cover">
                                    <button type="button" @click="removeImage(index)" class="absolute top-1 right-1 w-7 h-7 bg-black/60 text-white rounded-full flex items-center justify-center font-bold" aria-label="이미지 삭제">&times;</button>
                                </div>
                            </div>
                        </div>
                        <div class="w-full md:w-2/3">
                            <label class="block font-bold mb-1.5 text-xs md:text-sm">{{ editingPostId ? '등록한 비밀번호' : '수정용 비밀번호' }}</label>
                            <div class="flex flex-col sm:flex-row sm:items-center gap-2">
                                <input v-model="postForm.password" required maxlength="100" type="password" class="w-full sm:w-56 border p-2 rounded text-xs md:text-sm focus:outline-blue-500" placeholder="비밀번호 입력">
                                <span class="text-[10px] md:text-xs text-gray-400">※ 수정·삭제 시 동일한 비밀번호가 필요합니다.</span>
                            </div>
                        </div>
                        <p v-if="formError" class="text-sm text-red-600">{{ formError }}</p>
                        <div class="flex justify-end gap-2 pt-3">
                            <button type="button" @click="cancelWrite" class="border px-5 py-2 rounded text-gray-600 hover:bg-gray-50 text-xs md:text-sm transition">취소</button>
                            <button :disabled="submitting" type="submit" class="bg-blue-500 text-white px-5 py-2 rounded hover:bg-blue-600 text-xs md:text-sm transition disabled:opacity-50">
                                {{ submitting ? '처리 중...' : (editingPostId ? '수정' : '등록') }}
                            </button>
                        </div>
                    </form>
                </div>
            </transition>
        </main>

        <!-- [3. 모바일 전용 하단 탭 네비게이션 (md 미만에서 표시)] -->
        <nav class="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 flex justify-around py-2 z-40 shadow-inner">
            <button @click="changeView('home')" :class="{'text-blue-500': currentView === 'home', 'text-gray-500': currentView !== 'home'}" class="flex flex-col items-center justify-center flex-1 py-1">
                <i class="fas fa-home text-lg"></i>
                <span class="text-[10px] mt-1 font-medium">홈</span>
            </button>
            <button @click="changeView('map')" :class="{'text-blue-500': currentView === 'map', 'text-gray-500': currentView !== 'map'}" class="flex flex-col items-center justify-center flex-1 py-1">
                <i class="fas fa-map-location-dot text-lg"></i>
                <span class="text-[10px] mt-1 font-medium">지역 지도</span>
            </button>
            <button @click="changeView('board-list')" :class="{'text-blue-500': currentView.includes('board'), 'text-gray-500': !currentView.includes('board')}" class="flex flex-col items-center justify-center flex-1 py-1">
                <i class="fas fa-comments text-lg"></i>
                <span class="text-[10px] mt-1 font-medium">커뮤니티</span>
            </button>
        </nav>

        <!-- 푸터 (데스크톱에서만 노출하여 모바일 하단 공간 확보) -->
        <footer class="hidden md:block text-center text-xs text-gray-400 p-4 border-t shrink-0">
            &copy; localhub · made for Daejeon
        </footer>

        <!-- [4. 우측 하단 플로팅 챗봇 (FAB)] -->
        <!-- 모바일에서는 하단 탭 영역 위에 배치되도록 바텀 오프셋 조정 (bottom-20) -->
        <div class="fixed bottom-20 right-4 md:bottom-10 md:right-[calc(50%-550px)] z-50 flex flex-col items-end">
            
            <!-- 챗봇 창 (열렸을 때) -->
            <transition name="chat">
                <div v-if="isChatOpen" class="w-72 sm:w-80 md:w-96 h-[400px] md:h-[500px] bg-white rounded-lg shadow-2xl border border-gray-200 mb-4 flex flex-col overflow-hidden">
                    <!-- 헤더 -->
                    <div class="bg-blue-500 text-white p-3 flex justify-between items-center">
                        <h4 class="font-bold text-sm md:text-base">로컬 도우미 대롱이</h4>
                        <button @click="toggleChat" class="text-white hover:text-gray-200 text-2xl leading-none">
                            &times;
                        </button>
                    </div>
                    <!-- 대화 영역 -->
                    <div ref="chatWindow" class="flex-grow p-3 md:p-4 bg-gray-50 overflow-y-auto space-y-4 text-xs md:text-sm flex flex-col">
                        <div v-for="(msg, index) in chatMessages" :key="index"
                             :class="msg.role === 'user' ? 'bg-blue-500 text-white p-2.5 rounded-lg max-w-[85%] self-end ml-auto rounded-tr-none' : 'bg-blue-50 text-blue-800 p-2.5 rounded-lg max-w-[85%] self-start mr-auto rounded-tl-none'"
                             class="whitespace-pre-wrap break-words shadow-sm">
                            {{ msg.content }}
                        </div>
                        <!-- 챗봇 답변 로딩 표시 -->
                        <div v-if="chatLoading" class="bg-blue-50 text-blue-800 p-2.5 rounded-lg max-w-[85%] self-start mr-auto rounded-tl-none flex items-center gap-1 shadow-sm">
                            <span class="animate-bounce">●</span>
                            <span class="animate-bounce [animation-delay:0.2s]">●</span>
                            <span class="animate-bounce [animation-delay:0.4s]">●</span>
                        </div>
                    </div>
                    <!-- 입력 영역 -->
                    <div class="p-2.5 md:p-3 bg-white border-t flex gap-2">
                        <input v-model="chatInput" @keyup.enter="sendMessage" type="text" placeholder="대전에서 무엇을 찾으세요?" class="flex-1 border border-gray-300 rounded px-3 py-1.5 text-xs md:text-sm focus:outline-none focus:border-blue-400 bg-white">
                        <button @click="sendMessage" :disabled="chatLoading" class="bg-blue-500 text-white px-3 md:px-4 py-1.5 rounded text-xs md:text-sm hover:bg-blue-600 disabled:opacity-50 transition-colors">전송</button>
                    </div>
                </div>
            </transition>

            <!-- 챗봇 토글 버튼 -->
            <button @click="toggleChat" class="w-14 h-14 md:w-16 md:h-16 bg-white border-2 border-blue-500 text-blue-500 rounded-full shadow-lg flex items-center justify-center hover:bg-blue-50 transition-colors group overflow-hidden">
                <i v-if="isChatOpen" class="fas fa-times text-lg md:text-xl"></i>
                <svg v-else viewBox="0 0 300 300" width="86%" height="86%">
                    <circle cx="70" cy="104" r="36" style="fill: #1D4ED8;"></circle>
                    <circle cx="230" cy="104" r="36" style="fill: #1D4ED8;"></circle>
                    <circle cx="70" cy="108" r="18" style="fill: #FFFFFF;"></circle>
                    <circle cx="230" cy="108" r="18" style="fill: #FFFFFF;"></circle>
                    <circle cx="150" cy="170" r="110" style="fill: #60A5FA;"></circle>
                    <path d="M 58 182 Q 150 246 242 182 L 242 216 Q 150 274 58 216 Z" style="fill: #FFFFFF;"></path>
                    <path d="M 88 138 Q 150 112 212 138 Q 210 150 150 148 Q 90 150 88 138 Z" style="fill: #93C5FD; opacity: 0.6;"></path>
                    <circle cx="128" cy="160" r="11" style="fill: #1E3A8A;"></circle>
                    <circle cx="172" cy="160" r="11" style="fill: #1E3A8A;"></circle>
                    <circle cx="124" cy="156" r="3.5" style="fill: #FFFFFF;"></circle>
                    <circle cx="168" cy="156" r="3.5" style="fill: #FFFFFF;"></circle>
                    <ellipse cx="150" cy="190" rx="9" ry="6" style="fill: #1E3A8A;"></ellipse>
                    <path d="M 122 206 Q 150 226 178 206" style="fill: none; stroke: #1E3A8A; stroke-width: 5.5; stroke-linecap: round;"></path>
                    <circle cx="86" cy="192" r="15" style="fill: #FDA4AF; opacity: 0.5;"></circle>
                    <circle cx="214" cy="192" r="15" style="fill: #FDA4AF; opacity: 0.5;"></circle>
                    <g>
                        <circle cx="150" cy="70" r="38" style="fill: #1E40AF;"></circle>
                        <circle cx="118" cy="58" r="18" style="fill: #1E40AF;"></circle>
                        <circle cx="182" cy="58" r="18" style="fill: #1E40AF;"></circle>
                        <circle cx="126" cy="90" r="16" style="fill: #1E40AF;"></circle>
                        <circle cx="174" cy="90" r="16" style="fill: #1E40AF;"></circle>
                        <circle cx="150" cy="42" r="15" style="fill: #1E40AF;"></circle>
                        <circle cx="150" cy="98" r="14" style="fill: #1E40AF;"></circle>
                        <circle cx="132" cy="52" r="4" style="fill: #DBEAFE; opacity: 0.9;"></circle>
                        <circle cx="166" cy="48" r="3.5" style="fill: #DBEAFE; opacity: 0.9;"></circle>
                        <circle cx="150" cy="72" r="4.5" style="fill: #DBEAFE; opacity: 0.9;"></circle>
                        <circle cx="122" cy="78" r="3" style="fill: #DBEAFE; opacity: 0.9;"></circle>
                        <circle cx="176" cy="76" r="3.5" style="fill: #DBEAFE; opacity: 0.9;"></circle>
                        <circle cx="150" cy="96" r="3" style="fill: #DBEAFE; opacity: 0.9;"></circle>
                    </g>
                </svg>
            </button>
        </div>

    </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick, watch } from 'vue'

                const API_BASE_URL = `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api`;
                const LIKED_KEY = 'localhub-community-liked-posts';
                const REGION = '대전광역시';

                const currentView = ref('home');
                const selectedMapCategory = ref('39');
                const selectedMapCenter = ref(null);
                const selectedMapPlace = ref(null);
                const mapFrameEl = ref(null);
                const mapSearchPanelOpen = ref(true);

                const calendarModalOpen = ref(false);
                const calendarExpanded = ref(true);
                const calendarCursor = ref(new Date(new Date().getFullYear(), new Date().getMonth(), 1));
                const selectedCalendarDate = ref(new Date().toISOString().slice(0, 10));
                const calendarWeekdays = ['일', '월', '화', '수', '목', '금', '토'];

                const upcomingFestivals = ref([]);
                const upcomingEventsLoading = ref(false);
                const upcomingEventsError = ref('');
                const hotPlace = ref({ regions: [], selectedRegion: null, items: { 맛집: [], 관광지: [] } });
                const hotPlaceLoading = ref(false);
                const hotPlaceError = ref('');
                const mapFrameVersion = ref(0);

                // 지도 검색창에 검색어가 없을 때 보여줄, 게시글에서 많이 언급된 동네의 추천 장소(무작위 3곳)
                const hotRandomPlaces = ref([]);
                const hotRandomLoading = ref(false);

                // 홈 화면 "현재 인기게시물" - 조회수 TOP 3
                const popularPosts = ref([]);
                const popularPostsLoading = ref(false);


                const loadUpcomingEvents = async () => {
                    upcomingEventsLoading.value = true;
                    upcomingEventsError.value = '';
                    try {
                        // 캘린더에는 DB에 있는 축제/행사를 전부(과거 포함) 표시한다.
                        const response = await fetch(`${API_BASE_URL}/events/upcoming?limit=100&include_past=true`);
                        if (!response.ok) throw new Error(`이벤트 조회 실패: ${response.status}`);
                        const data = await response.json();
                        upcomingFestivals.value = (data.items || []).map(item => {
                            const start = new Date(`${item.start_date}T00:00:00`);
                            const end = item.end_date ? new Date(`${item.end_date}T00:00:00`) : null;
                            const month = new Intl.DateTimeFormat('en', { month: 'short' }).format(start).toUpperCase();
                            const today = new Date();
                            today.setHours(0, 0, 0, 0);
                            const diffDays = Math.ceil((start - today) / 86400000);
                            const status = diffDays > 0
                                ? `D-${diffDays}`
                                : (end && end >= today ? '진행 중' : (diffDays === 0 ? '오늘' : '종료'));
                            const calendarEndDate = end
                                ? new Date(end.getTime() + 86400000).toISOString().slice(0, 10)
                                : null;
                            return {
                                contentid: item.contentid,
                                title: item.title,
                                location: item.address || '위치 정보 없음',
                                period: item.end_date && item.end_date !== item.start_date
                                    ? `${item.start_date} ~ ${item.end_date}`
                                    : item.start_date,
                                status,
                                month,
                                day: String(start.getDate()).padStart(2, '0'),
                                startDate: item.start_date,
                                calendarEndDate,
                                firstimage: item.firstimage || '',
                                lat: Number(item.mapy),
                                lng: Number(item.mapx)
                            };
                        }).filter(item => Number.isFinite(item.lat) && Number.isFinite(item.lng));
                    } catch (error) {
                        console.error(error);
                        upcomingFestivals.value = [];
                        upcomingEventsError.value = '예정 이벤트를 불러오지 못했습니다.';
                    } finally {
                        upcomingEventsLoading.value = false;
                    }
                };

                const loadHotPlace = async () => {
                    hotPlaceLoading.value = true;
                    hotPlaceError.value = '';
                    try {
                        const response = await fetch(`${API_BASE_URL}/hot-place?limit_per_category=4`);
                        const data = await response.json().catch(() => null);
                        if (!response.ok) throw new Error(data?.detail || '핫 플레이스 조회에 실패했습니다.');
                        hotPlace.value = {
                            regions: (data.regions || []).map(region => ({
                                neighborhood: region.neighborhood,
                                mention_count: Number(region.mention_count || 0)
                            })),
                            selectedRegion: null,
                            items: { 맛집: [], 관광지: [] }
                        };
                        if (hotPlace.value.regions.length) {
                            await selectHotPlaceRegion(hotPlace.value.regions[0].neighborhood);
                        }
                    } catch (error) {
                        console.error(error);
                        hotPlaceError.value = '핫 플레이스를 불러오지 못했습니다.';
                    } finally {
                        hotPlaceLoading.value = false;
                    }
                };

                const loadHotRandomPlaces = async () => {
                    hotRandomLoading.value = true;
                    try {
                        const response = await fetch(`${API_BASE_URL}/hot-place/random?count=3`);
                        if (!response.ok) throw new Error(`추천 장소 조회 실패: ${response.status}`);
                        const data = await response.json();
                        hotRandomPlaces.value = (data || []).map(place => ({
                            ...place,
                            address: [place.addr1, place.addr2].filter(Boolean).join(' ')
                        }));
                    } catch (error) {
                        console.error(error);
                        hotRandomPlaces.value = [];
                    } finally {
                        hotRandomLoading.value = false;
                    }
                };

                const loadPopularPosts = async () => {
                    popularPostsLoading.value = true;
                    try {
                        const params = new URLSearchParams({ sort_by: 'views', page: '1', limit: '3' });
                        const response = await fetch(`${API_BASE_URL}/posts?${params.toString()}`);
                        if (!response.ok) throw new Error(`인기 게시물 조회 실패: ${response.status}`);
                        const data = await response.json();
                        popularPosts.value = data.items || [];
                    } catch (error) {
                        console.error(error);
                        popularPosts.value = [];
                    } finally {
                        popularPostsLoading.value = false;
                    }
                };

                const toDateKey = (date) => {
                    const year = date.getFullYear();
                    const month = String(date.getMonth() + 1).padStart(2, '0');
                    const day = String(date.getDate()).padStart(2, '0');
                    return `${year}-${month}-${day}`;
                };

                const calendarTitle = computed(() => `${calendarCursor.value.getFullYear()}년 ${calendarCursor.value.getMonth() + 1}월`);

                const eventsForDate = (dateKey) => upcomingFestivals.value.filter((event) => {
                    const start = event.startDate;
                    const endExclusive = event.calendarEndDate;
                    return start <= dateKey && (!endExclusive || dateKey < endExclusive);
                });

                const calendarDays = computed(() => {
                    const cursor = calendarCursor.value;
                    const first = new Date(cursor.getFullYear(), cursor.getMonth(), 1);
                    const gridStart = new Date(first);
                    gridStart.setDate(first.getDate() - first.getDay());
                    return Array.from({ length: 42 }, (_, index) => {
                        const date = new Date(gridStart);
                        date.setDate(gridStart.getDate() + index);
                        const dateKey = toDateKey(date);
                        const classes = {
                            'is-outside': date.getMonth() !== cursor.getMonth(),
                            'is-today': dateKey === toDateKey(new Date()),
                            'is-selected': dateKey === selectedCalendarDate.value,
                            'is-sunday': date.getDay() === 0,
                            'is-saturday': date.getDay() === 6
                        };
                        return { dateKey, day: date.getDate(), events: eventsForDate(dateKey), classes };
                    });
                });

                const selectedCalendarEvents = computed(() => eventsForDate(selectedCalendarDate.value));
                const selectedCalendarDateLabel = computed(() => {
                    const date = new Date(`${selectedCalendarDate.value}T00:00:00`);
                    return `${date.getMonth() + 1}월 ${date.getDate()}일`;
                });

                const moveCalendarMonth = (offset) => {
                    const current = calendarCursor.value;
                    calendarCursor.value = new Date(current.getFullYear(), current.getMonth() + offset, 1);
                };

                const goCalendarToday = () => {
                    const today = new Date();
                    calendarCursor.value = new Date(today.getFullYear(), today.getMonth(), 1);
                    selectedCalendarDate.value = toDateKey(today);
                };

                const selectCalendarDay = (day) => {
                    selectedCalendarDate.value = day.dateKey;
                    const selected = new Date(`${day.dateKey}T00:00:00`);
                    if (selected.getMonth() !== calendarCursor.value.getMonth()) {
                        calendarCursor.value = new Date(selected.getFullYear(), selected.getMonth(), 1);
                    }
                };

                const selectHotPlaceRegion = async (region) => {
                    hotPlaceLoading.value = true;
                    hotPlaceError.value = '';
                    try {
                        const response = await fetch(`${API_BASE_URL}/hot-place?region=${encodeURIComponent(region)}&limit_per_category=4`);
                        const data = await response.json().catch(() => null);
                        if (!response.ok) throw new Error(data?.detail || '핫 플레이스 조회에 실패했습니다.');
                        hotPlace.value = {
                            regions: (data.regions || []).map(item => ({ neighborhood: item.neighborhood, mention_count: Number(item.mention_count || 0) })),
                            selectedRegion: data.selected_region?.neighborhood || region,
                            items: {
                                맛집: (data.items?.맛집 || []).map(place => ({ ...place, address: [place.addr1, place.addr2].filter(Boolean).join(' ') })),
                                관광지: (data.items?.관광지 || []).map(place => ({ ...place, address: [place.addr1, place.addr2].filter(Boolean).join(' ') }))
                            }
                        };
                    } catch (error) { hotPlaceError.value = '핫 플레이스를 불러오지 못했습니다.'; }
                    finally { hotPlaceLoading.value = false; }
                };

                const openCalendarModal = () => { calendarModalOpen.value = true; };
                const closeCalendarModal = () => { calendarModalOpen.value = false; };
                const toggleHomeCalendar = () => { calendarExpanded.value = !calendarExpanded.value; };
                const isChatOpen = ref(false);
                const chatInput = ref('');
                const weatherLoading = ref(false);
                const weatherError = ref('');
                const weatherTemperature = ref(null);
                const weatherCode = ref(null);
                const weatherIsDay = ref(1);

                // 실시간 접속자 수 (웹소켓)
                const onlineCount = ref(null);
                let presenceSocket = null;
                const connectPresenceSocket = () => {
                    const wsBase = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/^http/, 'ws');
                    presenceSocket = new WebSocket(`${wsBase}/ws/presence`);
                    presenceSocket.onmessage = (event) => {
                        try {
                            const data = JSON.parse(event.data);
                            if (data.type === 'presence') onlineCount.value = data.count;
                        } catch (error) {
                            console.error('접속자 수 메시지 파싱 실패:', error);
                        }
                    };
                    presenceSocket.onclose = () => {
                        setTimeout(connectPresenceSocket, 3000);
                    };
                    presenceSocket.onerror = () => {
                        presenceSocket.close();
                    };
                };

                // 챗봇 기능 상태 변수 정의
                const chatMessages = ref([
                    { role: 'assistant', content: '안녕하슈! 대전광역시 관광 가이드 "대롱이"이슈. 무엇이든 질문해 주셔유!' }
                ]);
                const chatLoading = ref(false);
                const chatWindow = ref(null);

                const loading = ref(false);
                const submitting = ref(false);
                const errorMessage = ref('');
                const formError = ref('');
                const searchKeyword = ref('');
                const mapSearchKeyword = ref('');
                const mapSearchResults = ref([]);
                const mapSearchLoading = ref(false);
                const communitySearchKeyword = ref('');
                const unifiedSearchKeyword = ref('');
                const unifiedPlaceResults = ref([]);
                const unifiedSearchSubmitted = ref(false);
                const communitySearchResults = ref([]);
                const communitySearchSubmitted = ref(false);
                const searchLoading = ref(false);
                const searchError = ref('');
                const usingMockData = ref(false);
                const mapAutocompleteOpen = ref(false);
                const communityAutocompleteOpen = ref(false);
                const unifiedAutocompleteOpen = ref(false);
                const activeMapSuggestion = ref(-1);
                const activeCommunitySuggestion = ref(-1);
                const activeUnifiedSuggestion = ref(-1);
                let communitySearchTimer = null;
                let mapSearchTimer = null;
                let unifiedSearchTimer = null;
                const places = ref([]);
                const mockPosts = [
                    { id: 1001, title: '성심당 본점 평일 방문 후기', content: '평일 오전에는 대기 시간이 짧고 튀김소보로와 부추빵 재고도 넉넉했습니다.', tags: ['성심당', '빵집', '중구'], views: 42, likes: 7, created_at: '2026-07-12T10:20:00' },
                    { id: 1002, title: '한밭수목원 야간 산책 코스 추천', content: '엑스포다리 방향으로 이어지는 코스가 조용하고 야경도 보기 좋습니다.', tags: ['한밭수목원', '산책', '데이트'], views: 31, likes: 5, created_at: '2026-07-11T19:05:00' },
                    { id: 1003, title: '유성구 주말 행사 정리', content: '이번 주말 유성온천공원과 봉명동 일대에서 열리는 행사 정보를 모았습니다.', tags: ['유성구', '행사', '주말'], views: 58, likes: 9, created_at: '2026-07-10T14:30:00' },
                    { id: 1004, title: '둔산동 주차 편한 식당 추천', content: '가족 모임에 적당하고 주차 공간이 비교적 넉넉한 식당 위주로 정리했습니다.', tags: ['둔산동', '맛집', '주차'], views: 76, likes: 12, created_at: '2026-07-09T12:10:00' },
                    { id: 1005, title: '국립중앙과학관 전시 관람 팁', content: '오전 예약 후 자연사관부터 보면 혼잡을 피하기 좋고 어린이 체험관은 별도 확인이 필요합니다.', tags: ['과학관', '전시', '가족'], views: 29, likes: 4, created_at: '2026-07-08T09:40:00' }
                ];
                const likedPostIds = ref([]);
                const imageInput = ref(null);
                const boardPosts = ref([]);
                const selectedPost = ref(null);
                const editingPostId = ref(null);
                const pagination = reactive({ page: 1, size: 10, total: 0, total_pages: 1 });
                const postPeriod = ref('all');
                const postSortBy = ref('recent');
                const postSortOrder = ref('desc');
                const pageJumpInput = ref(1);
                const postForm = reactive({ title: '', content: '', password: '', tagsText: '', images: [] });

                const weatherDescriptions = {
                    0: '맑음', 1: '대체로 맑음', 2: '구름 조금', 3: '흐림',
                    45: '안개', 48: '서리 안개',
                    51: '약한 이슬비', 53: '이슬비', 55: '강한 이슬비',
                    56: '약한 어는 이슬비', 57: '강한 어는 이슬비',
                    61: '약한 비', 63: '비', 65: '강한 비',
                    66: '약한 어는 비', 67: '강한 어는 비',
                    71: '약한 눈', 73: '눈', 75: '강한 눈', 77: '싸락눈',
                    80: '약한 소나기', 81: '소나기', 82: '강한 소나기',
                    85: '약한 눈 소나기', 86: '강한 눈 소나기',
                    95: '뇌우', 96: '우박 동반 뇌우', 99: '강한 우박 동반 뇌우'
                };

                const weatherText = computed(() => {
                    if (weatherLoading.value && weatherTemperature.value === null) return '대전 날씨 조회 중';
                    if (weatherTemperature.value === null) return weatherError.value ? '날씨 조회 실패' : '대전 날씨';
                    const description = weatherDescriptions[weatherCode.value] || '날씨 정보';
                    return `대전 ${Math.round(weatherTemperature.value)}°C ${description}`;
                });

                const weatherIcon = computed(() => {
                    if (weatherLoading.value) return 'fa-spinner';
                    const code = Number(weatherCode.value);
                    if ([0, 1].includes(code)) return weatherIsDay.value ? 'fa-sun' : 'fa-moon';
                    if ([2, 3].includes(code)) return 'fa-cloud';
                    if ([45, 48].includes(code)) return 'fa-smog';
                    if ([71, 73, 75, 77, 85, 86].includes(code)) return 'fa-snowflake';
                    if ([95, 96, 99].includes(code)) return 'fa-cloud-bolt';
                    if ([51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82].includes(code)) return 'fa-cloud-rain';
                    return 'fa-cloud-sun';
                });

                const weatherIconColor = computed(() => {
                    const code = Number(weatherCode.value);
                    if ([0, 1].includes(code)) return weatherIsDay.value ? 'text-yellow-500' : 'text-indigo-500';
                    if ([95, 96, 99].includes(code)) return 'text-purple-500';
                    if ([71, 73, 75, 77, 85, 86].includes(code)) return 'text-sky-400';
                    if ([51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82].includes(code)) return 'text-blue-500';
                    return 'text-gray-500';
                });

                const loadWeather = async () => {
                    weatherLoading.value = true;
                    weatherError.value = '';
                    try {
                        const params = new URLSearchParams({
                            latitude: '36.3504',
                            longitude: '127.3845',
                            current: 'temperature_2m,weather_code,is_day',
                            timezone: 'Asia/Seoul'
                        });
                        const response = await fetch(`https://api.open-meteo.com/v1/forecast?${params.toString()}`);
                        if (!response.ok) throw new Error(`날씨 API 오류 (${response.status})`);
                        const data = await response.json();
                        if (!data.current || typeof data.current.temperature_2m !== 'number') {
                            throw new Error('현재 날씨 데이터가 없습니다.');
                        }
                        weatherTemperature.value = data.current.temperature_2m;
                        weatherCode.value = data.current.weather_code;
                        weatherIsDay.value = data.current.is_day;
                    } catch (error) {
                        console.error('날씨 조회 실패:', error);
                        weatherError.value = '날씨 정보를 불러오지 못했습니다. 클릭하여 다시 시도하세요.';
                    } finally {
                        weatherLoading.value = false;
                    }
                };

                const mapFrameSrc = computed(() => {
                    const params = new URLSearchParams({
                        category: selectedMapCategory.value,
                        v: String(mapFrameVersion.value),
                        apiBase: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
                        kakaoKey: import.meta.env.VITE_KAKAO_APP_KEY || ''
                    });
                    if (selectedMapCenter.value && Number.isFinite(selectedMapCenter.value.lat) && Number.isFinite(selectedMapCenter.value.lng)) {
                        params.set('lat', String(selectedMapCenter.value.lat));
                        params.set('lng', String(selectedMapCenter.value.lng));
                    }
                    if (selectedMapPlace.value?.contentid) params.set('focusId', String(selectedMapPlace.value.contentid));
                    return `./kakaomap.html?${params.toString()}`;
                });
                const mapFrameKey = computed(() => mapFrameSrc.value);

                const escapeHtml = (value) => String(value ?? '')
                    .replace(/&/g, '&amp;')
                    .replace(/</g, '&lt;')
                    .replace(/>/g, '&gt;')
                    .replace(/"/g, '&quot;')
                    .replace(/'/g, '&#039;');

                const highlightMapMatch = (value) => {
                    const escaped = escapeHtml(value);
                    const keyword = mapSearchKeyword.value.trim();
                    if (!keyword) return escaped;
                    const escapedKeyword = keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                    return escaped.replace(
                        new RegExp(`(${escapedKeyword})`, 'gi'),
                        '<mark class="bg-orange-100 text-orange-700 rounded px-0.5">$1</mark>'
                    );
                };

                const recentPosts = computed(() => boardPosts.value.slice(0, 4));
                const filteredPlaces = computed(() => mapSearchResults.value);
                const mapSuggestions = computed(() => mapSearchResults.value.slice(0, 8));
                const unifiedMapSuggestions = computed(() => {
                    return unifiedPlaceResults.value.slice(0, 6);
                });
                const communitySuggestions = computed(() => communitySearchResults.value.slice(0, 6));
                const visiblePages = computed(() => {
                    const start = Math.max(1, pagination.page - 2);
                    const end = Math.min(pagination.total_pages, start + 4);
                    return Array.from({ length: end - start + 1 }, (_, index) => start + index);
                });

                // posts 데이터 역직렬화 가공 (다중 이미지 및 필드 바인딩 안정화)
                const normalizePost = (post) => {
                    let parsedImages = [];
                    if (post.image) {
                        try {
                            parsedImages = JSON.parse(post.image);
                        } catch (e) {
                            parsedImages = [{ dataUrl: post.image, name: 'image' }];
                        }
                    }
                    return {
                        ...post,
                        region: REGION,
                        views: Number(post.views || 0),
                        likes: Number(post.likes || 0),
                        tags: Array.isArray(post.tags)
                            ? post.tags
                            : String(post.tags || '').split(',').map(tag => tag.trim()).filter(Boolean),
                        images: parsedImages,
                        updated_at: post.updated_at || post.created_at
                    };
                };

                const readIdList = (key) => {
                    try {
                        const value = JSON.parse(localStorage.getItem(key));
                        return Array.isArray(value) ? value.map(Number) : [];
                    } catch (error) {
                        return [];
                    }
                };

                const saveIdList = (key, values) => localStorage.setItem(key, JSON.stringify(values));

                const parseTags = (value) => [...new Set(value.split(',').map(tag => tag.trim().replace(/^#/, '')).filter(Boolean))].slice(0, 10);
                const isLiked = (postId) => likedPostIds.value.includes(Number(postId));

                const resetForm = () => {
                    postForm.title = '';
                    postForm.content = '';
                    postForm.password = '';
                    postForm.tagsText = '';
                    postForm.images = [];
                    if (imageInput.value) imageInput.value.value = '';
                    formError.value = '';
                };

                const openMapCategory = (contentTypeId) => {
                    selectedMapCenter.value = null;
                    selectedMapPlace.value = null;
                    selectedMapCategory.value = String(contentTypeId);
                    mapFrameVersion.value += 1;
                    currentView.value = 'map';
                    document.querySelector('main')?.scrollTo({ top: 0 });
                };


                const openEventOnMap = (event) => {
                    const lat = Number(event.lat);
                    const lng = Number(event.lng);
                    if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
                        console.error('이벤트 좌표가 올바르지 않습니다.', event);
                        return;
                    }
                    selectedMapCategory.value = '15';
                    selectedMapCenter.value = { lat, lng };
                    const place = {
                        contentid: event.contentid,
                        contenttypeid: '15',
                        name: event.title,
                        address: event.location,
                        lat,
                        lng,
                        firstimage: event.firstimage || ''
                    };
                    mapSearchKeyword.value = place.name;
                    mapSearchResults.value = [place];
                    selectedMapPlace.value = place;
                    mapFrameVersion.value += 1;
                    currentView.value = 'map';
                    document.querySelector('main')?.scrollTo({ top: 0 });
                };
                const changeView = async (viewName) => {
                    if (viewName === 'map') { selectedMapCategory.value = '39'; selectedMapCenter.value = null; selectedMapPlace.value = null; }
                    currentView.value = viewName;
                    document.querySelector('main')?.scrollTo({ top: 0 });
                    if (viewName === 'board-list') await loadPosts();
                };

                const fetchMapPlaces = async () => {
                    const keyword = mapSearchKeyword.value.trim();
                    activeMapSuggestion.value = -1;
                    if (!keyword) {
                        mapSearchResults.value = [];
                        return;
                    }
                    mapSearchLoading.value = true;
                    try {
                        const params = new URLSearchParams({ search: keyword, page: '1', limit: '8' });
                        const response = await fetch(`${API_BASE_URL}/tours?${params.toString()}`);
                        if (!response.ok) throw new Error(`장소 검색 실패: ${response.status}`);
                        const data = await response.json();
                        mapSearchResults.value = (data.items || []).map(item => ({
                            contentid: item.contentid,
                            contenttypeid: item.contenttypeid,
                            name: item.title,
                            address: [item.addr1, item.addr2].filter(Boolean).join(' '),
                            tags: [],
                            lat: Number(item.mapy),
                            lng: Number(item.mapx),
                            firstimage: item.firstimage || ''
                        }));
                    } catch (error) {
                        console.error(error);
                        mapSearchResults.value = [];
                    } finally {
                        mapSearchLoading.value = false;
                    }
                };

                const handleMapAutocomplete = () => {
                    clearTimeout(mapSearchTimer);
                    mapSearchTimer = setTimeout(fetchMapPlaces, 250);
                };

                const searchMapPlaces = async () => {
                    clearTimeout(mapSearchTimer);
                    await fetchMapPlaces();
                };

                const selectMapSuggestion = (place) => {
                    mapSearchKeyword.value = place.name;
                    activeMapSuggestion.value = -1;
                    openPlaceOnMap(place);
                };

                const moveMapSuggestion = (direction) => {
                    const count = mapSuggestions.value.length;
                    if (!count) return;
                    activeMapSuggestion.value = (activeMapSuggestion.value + direction + count) % count;
                };

                const selectActiveMapSuggestion = () => {
                    const place = mapSuggestions.value[activeMapSuggestion.value] || mapSuggestions.value[0];
                    if (place) selectMapSuggestion(place);
                };

                const openPlaceOnMap = (place) => {
                    mapSearchKeyword.value = place.name;
                    mapSearchResults.value = [place];

                    // 지도가 이미 떠 있으면 iframe을 통째로 새로 로드하지 않고, 이미 로드된 지도에
                    // "이 위치로 이동해줘"만 postMessage로 전달한다 (마커/노선 재생성 비용을 아낌).
                    if (currentView.value === 'map' && mapFrameEl.value?.contentWindow) {
                        mapFrameEl.value.contentWindow.postMessage({
                            type: 'localhub:focus-place',
                            lat: place.lat,
                            lng: place.lng,
                            focusId: place.contentid,
                            category: place.contenttypeid ? String(place.contenttypeid) : null
                        }, window.location.origin);
                        return;
                    }

                    selectedMapPlace.value = place;
                    if (place.contenttypeid) selectedMapCategory.value = String(place.contenttypeid);
                    if (Number.isFinite(place.lat) && Number.isFinite(place.lng)) {
                        selectedMapCenter.value = { lat: place.lat, lng: place.lng };
                    }
                    mapFrameVersion.value += 1;
                    currentView.value = 'map';
                    document.querySelector('main')?.scrollTo({ top: 0 });
                };

                const openHotPlaceOnMap = (place) => openPlaceOnMap({
                    contentid: place.contentid,
                    name: place.title,
                    address: [place.addr1, place.addr2].filter(Boolean).join(' '),
                    contenttypeid: place.contenttypeid,
                    lat: Number(place.mapy),
                    lng: Number(place.mapx),
                    firstimage: place.firstimage || ''
                });


                // ------------------------------------------------------------------
                // 지도 길찾기 (출발지 -> 도착지 버스 경로 탐색, /api/routes/plan 사용)
                // ------------------------------------------------------------------
                const busPlanMode = ref(false);
                const busStart = ref({ keyword: '', place: null, results: [], loading: false, open: false });
                const busEnd = ref({ keyword: '', place: null, results: [], loading: false, open: false });
                const busPlans = ref([]);
                const busPlanLoading = ref(false);
                const busPlanError = ref('');
                const busPlanMessage = ref('');
                const activeBusPlanIndex = ref(-1);
                const busSearchTimers = { start: null, end: null };
                // 길찾기 모드에서 지도 핀 클릭 시 값이 채워질 입력칸 ('start' | 'end')
                // 지도(iframe)를 클릭하는 순간 입력칸의 포커스는 풀리므로,
                // "마지막으로 커서를 놓았던 칸"을 별도로 기억해둔다.
                const activeBusField = ref('start');

                const busField = (which) => (which === 'start' ? busStart.value : busEnd.value);

                const mapTourItemToBusPlace = (item) => ({
                    contentid: item.contentid,
                    name: item.title,
                    address: [item.addr1, item.addr2].filter(Boolean).join(' '),
                    lat: Number(item.mapy),
                    lng: Number(item.mapx)
                });

                const fetchBusPlaces = async (which) => {
                    const field = busField(which);
                    const keyword = field.keyword.trim();
                    if (!keyword) { field.results = []; return; }
                    field.loading = true;
                    try {
                        const params = new URLSearchParams({ search: keyword, page: '1', limit: '6' });
                        const response = await fetch(`${API_BASE_URL}/tours?${params.toString()}`);
                        if (!response.ok) throw new Error(`장소 검색 실패: ${response.status}`);
                        const data = await response.json();
                        field.results = (data.items || [])
                            .map(mapTourItemToBusPlace)
                            .filter(place => Number.isFinite(place.lat) && Number.isFinite(place.lng));
                        field.open = true;
                    } catch (error) {
                        console.error(error);
                        field.results = [];
                    } finally {
                        field.loading = false;
                    }
                };

                const handleBusAutocomplete = (which) => {
                    const field = busField(which);
                    field.place = null; // 키워드를 수정하면 이전에 선택했던 장소는 무효화
                    clearTimeout(busSearchTimers[which]);
                    busSearchTimers[which] = setTimeout(() => fetchBusPlaces(which), 250);
                };

                const selectBusPlace = (which, place) => {
                    const field = busField(which);
                    field.keyword = place.name;
                    field.place = place;
                    field.results = [];
                    field.open = false;
                };

                const swapBusPoints = () => {
                    const temp = { keyword: busStart.value.keyword, place: busStart.value.place };
                    busStart.value.keyword = busEnd.value.keyword;
                    busStart.value.place = busEnd.value.place;
                    busEnd.value.keyword = temp.keyword;
                    busEnd.value.place = temp.place;
                    busStart.value.results = [];
                    busEnd.value.results = [];
                    if (busPlans.value.length) requestBusPlan();
                };

                // 목록에서 직접 고르지 않고 바로 길찾기를 누른 경우, 첫 번째 검색 결과로 자동 확정한다.
                const resolveBusPlace = async (which) => {
                    const field = busField(which);
                    if (field.place) return field.place;
                    const keyword = field.keyword.trim();
                    if (!keyword) return null;
                    const params = new URLSearchParams({ search: keyword, page: '1', limit: '1' });
                    const response = await fetch(`${API_BASE_URL}/tours?${params.toString()}`);
                    if (!response.ok) return null;
                    const data = await response.json();
                    const item = (data.items || [])[0];
                    if (!item) return null;
                    const place = mapTourItemToBusPlace(item);
                    if (!Number.isFinite(place.lat) || !Number.isFinite(place.lng)) return null;
                    selectBusPlace(which, place);
                    return place;
                };

                const requestBusPlan = async () => {
                    busPlanError.value = '';
                    busPlanMessage.value = '';
                    activeBusPlanIndex.value = -1;
                    if (!busStart.value.keyword.trim() || !busEnd.value.keyword.trim()) {
                        busPlanError.value = '출발지와 도착지를 모두 입력해주세요.';
                        return;
                    }
                    busPlanLoading.value = true;
                    busPlans.value = [];
                    try {
                        const [startPlace, endPlace] = await Promise.all([
                            resolveBusPlace('start'),
                            resolveBusPlace('end')
                        ]);
                        if (!startPlace) throw new Error('출발지를 찾지 못했습니다. 다른 검색어로 시도해보세요.');
                        if (!endPlace) throw new Error('도착지를 찾지 못했습니다. 다른 검색어로 시도해보세요.');
                        const params = new URLSearchParams({
                            start_lat: String(startPlace.lat), start_lng: String(startPlace.lng),
                            end_lat: String(endPlace.lat), end_lng: String(endPlace.lng)
                        });
                        const response = await fetch(`${API_BASE_URL}/routes/plan?${params.toString()}`);
                        if (!response.ok) throw new Error(`경로 탐색 실패: ${response.status}`);
                        const data = await response.json();
                        busPlans.value = data.plans || [];
                        busPlanMessage.value = busPlans.value.length ? '' : (data.message || '조건에 맞는 버스 경로를 찾지 못했습니다.');
                        // 첫 번째 추천 경로를 지도에 바로 표시
                        if (busPlans.value.length) showBusPlanOnMap(busPlans.value[0], 0);
                    } catch (error) {
                        console.error(error);
                        busPlanError.value = error.message || '버스 경로 탐색 중 오류가 발생했습니다.';
                    } finally {
                        busPlanLoading.value = false;
                    }
                };

                const showBusPlanOnMap = (plan, index) => {
                    activeBusPlanIndex.value = index;
                    const startPlace = busStart.value.place;
                    const endPlace = busEnd.value.place;
                    if (!startPlace || !endPlace || !mapFrameEl.value?.contentWindow) return;
                    mapFrameEl.value.contentWindow.postMessage({
                        type: 'localhub:show-bus-plan',
                        plan: JSON.parse(JSON.stringify(plan)),
                        origin: { lat: startPlace.lat, lng: startPlace.lng, name: startPlace.name },
                        destination: { lat: endPlace.lat, lng: endPlace.lng, name: endPlace.name }
                    }, window.location.origin);
                };

                const clearBusPlans = () => {
                    busPlans.value = [];
                    busPlanMessage.value = '';
                    busPlanError.value = '';
                    activeBusPlanIndex.value = -1;
                    mapFrameEl.value?.contentWindow?.postMessage({ type: 'localhub:clear-bus-plan' }, window.location.origin);
                };

                const setBusPlanMode = (on) => {
                    busPlanMode.value = on;
                    if (on) {
                        // 비어 있는 칸을 핀 입력 대상으로 지정 (출발지 우선)
                        activeBusField.value = !busStart.value.keyword.trim() ? 'start'
                            : (!busEnd.value.keyword.trim() ? 'end' : 'start');
                    } else {
                        clearBusPlans();
                    }
                };

                const formatWalkDistance = (km) => {
                    if (km === null || km === undefined) return '-';
                    return km < 1 ? `${Math.round(km * 1000)}m` : `${km.toFixed(1)}km`;
                };

                const getPostSearchParams = (keyword) => {
                    const normalized = keyword.trim();
                    if (normalized.startsWith('#')) {
                        const tag = normalized.slice(1).replace(/\s/g, '');
                        return tag ? { tag } : {};
                    }
                    return normalized ? { search: normalized } : {};
                };

                const filterMockPosts = (keyword) => {
                    const normalized = keyword.trim().toLowerCase();
                    if (!normalized) return mockPosts.map(normalizePost);
                    if (normalized.startsWith('#')) {
                        const tag = normalized.slice(1).replace(/\s/g, '');
                        return mockPosts.filter(post =>
                            (post.tags || []).some(value => String(value).replace(/^#/, '').toLowerCase() === tag)
                        ).map(normalizePost);
                    }
                    return mockPosts.filter(post =>
                        [post.title, post.content, ...(post.tags || [])]
                            .some(value => String(value).toLowerCase().includes(normalized))
                    ).map(normalizePost);
                };

                const searchCommunityPosts = async () => {
                    communitySearchSubmitted.value = true;
                    searchLoading.value = true;
                    searchError.value = '';
                    const keyword = communitySearchKeyword.value.trim();
                    try {
                        const params = new URLSearchParams(getPostSearchParams(keyword));
                        const response = await fetch(`${API_BASE_URL}/posts?${params.toString()}`, {
                            signal: AbortSignal.timeout ? AbortSignal.timeout(1800) : undefined
                        });
                        const data = await response.json().catch(() => null);
                        if (!response.ok) throw new Error(data?.detail || '게시글 검색에 실패했습니다.');
                        communitySearchResults.value = (Array.isArray(data) ? data : (data.items || [])).map(normalizePost);
                        usingMockData.value = false;
                    } catch (error) {
                        console.info('서버 미연결: 샘플 게시글 데이터로 검색합니다.', error);
                        communitySearchResults.value = filterMockPosts(keyword);
                        usingMockData.value = true;
                        searchError.value = '';
                    } finally {
                        searchLoading.value = false;
                    }
                };

                const handleCommunityAutocomplete = () => {
                    communityAutocompleteOpen.value = true;
                    activeCommunitySuggestion.value = -1;
                    clearTimeout(communitySearchTimer);
                    const keyword = communitySearchKeyword.value.trim();
                    if (!keyword) {
                        communitySearchResults.value = [];
                        searchLoading.value = false;
                        return;
                    }
                    communitySearchTimer = setTimeout(searchCommunityPosts, 220);
                };

                const selectCommunitySuggestion = (post) => {
                    communityAutocompleteOpen.value = false;
                    activeCommunitySuggestion.value = -1;
                    openPost(post.id);
                };

                const moveCommunitySuggestion = (direction) => {
                    const count = communitySuggestions.value.length;
                    if (!count) return;
                    communityAutocompleteOpen.value = true;
                    activeCommunitySuggestion.value = (activeCommunitySuggestion.value + direction + count) % count;
                };

                const selectActiveCommunitySuggestion = async () => {
                    if (!communitySuggestions.value.length && communitySearchKeyword.value.trim()) {
                        await searchCommunityPosts();
                    }
                    const post = communitySuggestions.value[activeCommunitySuggestion.value] || communitySuggestions.value[0];
                    if (post) selectCommunitySuggestion(post);
                };

                const handleUnifiedAutocomplete = () => {
                    unifiedAutocompleteOpen.value = true;
                    activeUnifiedSuggestion.value = -1;
                    communitySearchKeyword.value = unifiedSearchKeyword.value;
                    clearTimeout(unifiedSearchTimer);
                    const keyword = unifiedSearchKeyword.value.trim();
                    if (!keyword) {
                        communitySearchResults.value = [];
                        unifiedPlaceResults.value = [];
                        unifiedSearchSubmitted.value = false;
                        searchLoading.value = false;
                        return;
                    }
                    // 입력 중에는 자동완성 팝업만 갱신한다. 아래 상세 결과는 Enter로 확정할 때 표시한다.
                    unifiedSearchSubmitted.value = false;
                    unifiedSearchTimer = setTimeout(() => {
                        searchCommunityPosts();
                        searchUnifiedPlaces(keyword);
                    }, 220);
                };

                const unifiedSuggestions = computed(() => [
                    ...unifiedMapSuggestions.value.map(item => ({ type: 'place', item })),
                    ...communitySuggestions.value.map(item => ({ type: 'post', item }))
                ]);

                const selectUnifiedSuggestion = (suggestion) => {
                    unifiedAutocompleteOpen.value = false;
                    activeUnifiedSuggestion.value = -1;
                    if (suggestion.type === 'place') {
                        unifiedSearchKeyword.value = suggestion.item.name;
                        openPlaceOnMap(suggestion.item);
                        return;
                    }
                    openPost(suggestion.item.id);
                };

                const moveUnifiedSuggestion = (direction) => {
                    const count = unifiedSuggestions.value.length;
                    if (!count) return;
                    unifiedAutocompleteOpen.value = true;
                    activeUnifiedSuggestion.value = (activeUnifiedSuggestion.value + direction + count) % count;
                };

                const selectActiveUnifiedSuggestion = async () => {
                    if (!communitySuggestions.value.length && unifiedSearchKeyword.value.trim()) {
                        communitySearchKeyword.value = unifiedSearchKeyword.value;
                        await searchCommunityPosts();
                    }
                    const suggestion = unifiedSuggestions.value[activeUnifiedSuggestion.value] || unifiedSuggestions.value[0];
                    if (suggestion) selectUnifiedSuggestion(suggestion);
                };

                const searchUnifiedPlaces = async (keyword = unifiedSearchKeyword.value.trim()) => {
                    try {
                        const params = new URLSearchParams({ search: keyword, page: '1', limit: '8' });
                        const response = await fetch(`${API_BASE_URL}/tours?${params.toString()}`);
                        if (!response.ok) throw new Error('장소 검색 실패');
                        const data = await response.json();
                        unifiedPlaceResults.value = (data.items || []).map(item => ({ contentid: item.contentid, contenttypeid: item.contenttypeid, name: item.title, address: [item.addr1, item.addr2].filter(Boolean).join(' '), tags: [], lat: Number(item.mapy), lng: Number(item.mapx), firstimage: item.firstimage || '' }));
                    } catch (error) { unifiedPlaceResults.value = []; }
                };

                const submitUnifiedSearch = async () => {
                    const keyword = unifiedSearchKeyword.value.trim();
                    if (!keyword) return;
                    clearTimeout(unifiedSearchTimer);
                    unifiedSearchSubmitted.value = true;
                    unifiedAutocompleteOpen.value = false;
                    communitySearchKeyword.value = keyword;
                    await Promise.all([searchCommunityPosts(), searchUnifiedPlaces(keyword)]);
                };

                const loadPosts = async () => {
                    loading.value = true;
                    errorMessage.value = '';
                    const keyword = searchKeyword.value.trim();

                    try {
                        const params = new URLSearchParams(getPostSearchParams(keyword));
                        params.set('period', postPeriod.value);
                        params.set('sort_by', postSortBy.value);
                        params.set('sort_order', postSortOrder.value);
                        params.set('page', String(pagination.page));
                        params.set('limit', String(pagination.size));
                        const response = await fetch(`${API_BASE_URL}/posts?${params.toString()}`, {
                            signal: AbortSignal.timeout ? AbortSignal.timeout(1800) : undefined
                        });
                        const data = await response.json().catch(() => null);
                        if (!response.ok) throw new Error(data?.detail || '게시글 목록 조회에 실패했습니다.');

                        const items = Array.isArray(data) ? data : (data.items || []);
                        usingMockData.value = false;
                        pagination.total = Number(data.total ?? items.length);
                        pagination.total_pages = Number(data.total_pages ?? Math.max(1, Math.ceil(items.length / pagination.size)));
                        pagination.page = Number(data.page ?? pagination.page);
                        pageJumpInput.value = pagination.page;
                        boardPosts.value = items.map(normalizePost);
                    } catch (error) {
                        console.info('서버 미연결: 샘플 게시글 목록을 표시합니다.', error);
                        const allPosts = filterMockPosts(keyword).sort((a, b) => {
                            const direction = postSortOrder.value === 'asc' ? 1 : -1;
                            const values = {
                                id: [a.id, b.id], title: [a.title, b.title], views: [a.views || 0, b.views || 0],
                                likes: [a.likes || 0, b.likes || 0], recent: [a.created_at, b.created_at]
                            }[postSortBy.value];
                            return typeof values[0] === 'string' ? direction * values[0].localeCompare(values[1]) : direction * (values[0] - values[1]);
                        });
                        usingMockData.value = true;
                        errorMessage.value = '';
                        pagination.total = allPosts.length;
                        pagination.total_pages = Math.max(1, Math.ceil(allPosts.length / pagination.size));
                        if (pagination.page > pagination.total_pages) pagination.page = pagination.total_pages;
                        const startIndex = (pagination.page - 1) * pagination.size;
                        boardPosts.value = allPosts.slice(startIndex, startIndex + pagination.size);
                    } finally {
                        loading.value = false;
                    }
                };

                const searchPosts = async () => { pagination.page = 1; await loadPosts(); };
                const changePostFilters = async () => { pagination.page = 1; await loadPosts(); };
                const togglePostSort = async (field) => {
                    postSortOrder.value = postSortBy.value === field && postSortOrder.value === 'desc' ? 'asc' : 'desc';
                    postSortBy.value = field;
                    pagination.page = 1;
                    await loadPosts();
                };
                const changePageSize = async () => {
                    pagination.page = 1;
                    await loadPosts();
                };
                const goToPage = async (page) => {
                    if (page < 1 || page > pagination.total_pages || page === pagination.page) return;
                    pagination.page = page;
                    await loadPosts();
                };
                const jumpToPage = async () => {
                    const page = Number(pageJumpInput.value);
                    if (!Number.isInteger(page) || page < 1 || page > pagination.total_pages) {
                        pageJumpInput.value = pagination.page;
                        return;
                    }
                    await goToPage(page);
                };

                const openPost = async (postId) => {
                    loading.value = true;
                    errorMessage.value = '';
                    const mockPost = mockPosts.find(post => Number(post.id) === Number(postId));

                    try {
                        const response = await fetch(`${API_BASE_URL}/posts/${postId}`, {
                            signal: AbortSignal.timeout ? AbortSignal.timeout(1800) : undefined
                        });
                        const data = await response.json().catch(() => null);
                        if (!response.ok) throw new Error(data?.detail || '게시글을 찾을 수 없습니다.');
                        selectedPost.value = normalizePost(data);
                        usingMockData.value = false;
                    } catch (error) {
                        if (!mockPost) {
                            alert('게시글을 불러올 수 없습니다.');
                            return;
                        }
                        selectedPost.value = normalizePost(mockPost);
                        usingMockData.value = true;
                    } finally {
                        loading.value = false;
                    }

                    currentView.value = 'board-detail';
                    document.querySelector('main')?.scrollTo({ top: 0 });
                };

                const openWriteView = () => {
                    editingPostId.value = null;
                    resetForm();
                    currentView.value = 'board-write';
                };

                const openEditView = () => {
                    if (!selectedPost.value) return;
                    editingPostId.value = selectedPost.value.id;
                    postForm.title = selectedPost.value.title;
                    postForm.content = selectedPost.value.content;
                    postForm.tagsText = (selectedPost.value.tags || []).join(', ');
                    postForm.images = [...(selectedPost.value.images || [])];
                    postForm.password = '';
                    formError.value = '';
                    currentView.value = 'board-write';
                };

                const cancelWrite = () => {
                    const target = editingPostId.value ? 'board-detail' : 'board-list';
                    resetForm();
                    editingPostId.value = null;
                    changeView(target);
                };

                const submitPost = async () => {
                    formError.value = '';
                    if (!postForm.title || !postForm.content || !postForm.password) {
                        formError.value = '제목, 내용, 비밀번호를 모두 입력하세요.';
                        return;
                    }
                    if (postForm.password.length < 4) {
                        formError.value = '비밀번호는 최소 4자여야 합니다.';
                        return;
                    }

                    submitting.value = true;
                    try {
                        const isEditing = Boolean(editingPostId.value);
                        const url = isEditing
                            ? `${API_BASE_URL}/posts/${editingPostId.value}`
                            : `${API_BASE_URL}/posts`;

                        // 다중 이미지 배열 직렬화 처리 통합
                        const imageString = postForm.images.length ? JSON.stringify(postForm.images) : null;

                        const response = await fetch(url, {
                            method: isEditing ? 'PUT' : 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                title: postForm.title,
                                content: postForm.content,
                                password: postForm.password,
                                tags: parseTags(postForm.tagsText).join(',') || null,
                                image: imageString
                            })
                        });
                        const data = await response.json().catch(() => null);

                        if (!response.ok) {
                            throw new Error(data?.detail || '게시글 저장에 실패했습니다.');
                        }

                        selectedPost.value = normalizePost(data);
                        resetForm();
                        editingPostId.value = null;
                        currentView.value = 'board-detail';
                        alert(isEditing ? '게시글이 수정되었습니다.' : '게시글이 등록되었습니다.');
                        await loadPosts();
                    } catch (error) {
                        formError.value = error.message;
                    } finally {
                        submitting.value = false;
                    }
                };

                const deletePost = async () => {
                    if (!selectedPost.value) return;
                    const password = prompt('게시글 삭제 비밀번호를 입력하세요.');
                    if (password === null) return;
                    if (!confirm('게시글을 삭제하시겠습니까?')) return;

                    try {
                        const response = await fetch(`${API_BASE_URL}/posts/${selectedPost.value.id}`, {
                            method: 'DELETE',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ password })
                        });
                        const data = await response.json().catch(() => null);

                        if (!response.ok) {
                            throw new Error(data?.detail || '게시글 삭제에 실패했습니다.');
                        }

                        const deletedId = Number(selectedPost.value.id);
                        likedPostIds.value = likedPostIds.value.filter(id => id !== deletedId);
                        saveIdList(LIKED_KEY, likedPostIds.value);

                        selectedPost.value = null;
                        pagination.page = 1;
                        await changeView('board-list');
                        alert('게시글이 삭제되었습니다.');
                    } catch (error) {
                        alert(error.message);
                    }
                };

                const toggleLike = async () => {
                    if (!selectedPost.value) return;
                    const id = Number(selectedPost.value.id);

                    if (isLiked(id)) {
                        alert('현재 백엔드 API는 좋아요 취소를 지원하지 않습니다.');
                        return;
                    }

                    try {
                        const response = await fetch(`${API_BASE_URL}/posts/${id}/like`, {
                            method: 'POST'
                        });
                        const data = await response.json().catch(() => null);

                        if (!response.ok) {
                            throw new Error(data?.detail || '좋아요 처리에 실패했습니다.');
                        }

                        likedPostIds.value = [...likedPostIds.value, id];
                        saveIdList(LIKED_KEY, likedPostIds.value);
                        selectedPost.value = normalizePost(data);
                    } catch (error) {
                        alert(error.message);
                    }
                };

                const handleImageUpload = async (event) => {
                    const files = Array.from(event.target.files || []);
                    if (postForm.images.length + files.length > 3) {
                        formError.value = '이미지는 최대 3장까지 첨부할 수 있습니다.';
                        event.target.value = '';
                        return;
                    }
                    for (const file of files) {
                        if (!file.type.startsWith('image/')) continue;
                        if (file.size > 2 * 1024 * 1024) {
                            formError.value = '이미지 한 장의 크기는 2MB 이하여야 합니다.';
                            continue;
                        }
                        const dataUrl = await new Promise((resolve, reject) => {
                            const reader = new FileReader();
                            reader.onload = () => resolve(reader.result);
                            reader.onerror = reject;
                            reader.readAsDataURL(file);
                        });
                        postForm.images.push({ name: file.name, dataUrl });
                    }
                    event.target.value = '';
                };

                const removeImage = (index) => postForm.images.splice(index, 1);

                const parseApiDate = (value) => {
                    if (!value) return null;
                    const normalized = String(value).includes('T') ? String(value) : String(value).replace(' ', 'T');
                    const date = new Date(normalized);
                    return Number.isNaN(date.getTime()) ? null : date;
                };
                const formatDate = (value) => {
                    const date = parseApiDate(value);
                    return date ? new Intl.DateTimeFormat('ko-KR', { year: '2-digit', month: '2-digit', day: '2-digit' }).format(date) : '';
                };
                const formatDateTime = (value) => {
                    const date = parseApiDate(value);
                    return date ? new Intl.DateTimeFormat('ko-KR', { dateStyle: 'medium', timeStyle: 'short' }).format(date) : '';
                };
                
                const scrollChatToBottom = () => {
                    nextTick(() => {
                        if (chatWindow.value) {
                            chatWindow.value.scrollTop = chatWindow.value.scrollHeight;
                        }
                    });
                };

                const toggleChat = () => { 
                    isChatOpen.value = !isChatOpen.value; 
                    if (isChatOpen.value) {
                        scrollChatToBottom();
                    }
                };

                // 실시간 백엔드 챗봇 API 연동 처리
                const sendMessage = async () => {
                    const text = chatInput.value.trim();
                    if (!text || chatLoading.value) return;

                    chatMessages.value.push({ role: 'user', content: text });
                    chatInput.value = '';
                    scrollChatToBottom();

                    chatLoading.value = true;
                    try {
                        const response = await fetch(`${API_BASE_URL}/chat`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                messages: chatMessages.value.map(msg => ({
                                    role: msg.role,
                                    content: msg.content
                                }))
                            }),
                            signal: AbortSignal.timeout ? AbortSignal.timeout(60000) : undefined
                        });
                        if (!response.ok) throw new Error('챗봇 응답 수신에 실패했습니다.');
                        
                        const data = await response.json();
                        const replyContent = data.content || data.reply || '답변을 가져오는 데 문제가 발생했습니다.';
                        chatMessages.value.push({ role: 'assistant', content: replyContent });
                    } catch (error) {
                        console.error('Chat API Error:', error);
                        chatMessages.value.push({ 
                            role: 'assistant', 
                            content: '백엔드 서버 또는 OpenAI 연동에 에러가 발생했슈... API 키 설정을 확인하거나 서버(http://localhost:8000) 상태를 점검해봐 주셔유!' 
                        });
                    } finally {
                        chatLoading.value = false;
                        scrollChatToBottom();
                    }
                };

                onMounted(() => {
                    window.addEventListener('message', (event) => {
                        if (event.origin !== window.location.origin || event.data?.type !== 'localhub:place-selected') return;
                        const poi = event.data.place;
                        const place = {
                            contentid: poi.contentid,
                            contenttypeid: poi.contenttypeid,
                            name: poi.title,
                            address: [poi.addr1, poi.addr2].filter(Boolean).join(' '),
                            tags: [],
                            lat: Number(poi.mapy),
                            lng: Number(poi.mapx),
                            firstimage: poi.firstimage || ''
                        };
                        // 길찾기 모드: 마지막으로 커서를 놓았던 입력칸에 클릭한 핀의 주소를 채운다.
                        if (busPlanMode.value) {
                            const which = activeBusField.value || 'start';
                            const field = busField(which);
                            field.keyword = place.address || place.name; // 주소가 없는 장소는 이름으로 대체
                            field.place = place;
                            field.results = [];
                            field.open = false;
                            // 반대쪽 칸이 비어 있으면 다음 핀 클릭 대상을 그쪽으로 자동 전환
                            const other = which === 'start' ? 'end' : 'start';
                            if (!busField(other).keyword.trim()) activeBusField.value = other;
                            return;
                        }
                        mapSearchKeyword.value = place.name;
                        mapSearchResults.value = [place];
                        activeMapSuggestion.value = 0;
                    });
                    likedPostIds.value = readIdList(LIKED_KEY);
                    loadWeather();
                    loadPosts();
                    loadUpcomingEvents();
                    loadHotPlace();
                    loadHotRandomPlaces();
                    loadPopularPosts();
                    connectPresenceSocket();
                });


</script>
