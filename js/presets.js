/**
 * presets.js - Curated System-One / System-Two Scenario Templates
 * for answerr (answerr.me)
 */

const SCENARIO_PRESETS = [
  {
    id: 'api-security-safe',
    category: 'Cybersecurity',
    categoryTr: 'Siber Güvenlik',
    icon: '🛡️',
    title: 'Authenticated Admin Request',
    titleTr: 'Doğrulanmış Yönetici İsteği',
    prompt: 'Kullanıcı rolü "admin", oturum geçerli, istek sıklığı saniyede 1.5, hata denemesi 0. Bu operasyonun yürütülmesine onay verilsin mi?',
    promptEn: 'User role "admin", authenticated=true, request frequency 1.5 req/s, 0 failed attempts. Should execution be permitted?'
  },
  {
    id: 'api-security-attack',
    category: 'Cybersecurity',
    categoryTr: 'Siber Güvenlik',
    icon: '🚨',
    title: 'DDoS Burst from Anonymous IP',
    titleTr: 'Anonim IP Şüpheli DDoS Trafiği',
    prompt: 'Anonim konuk (guest) kullanıcı, doğrulama yok, son 1 dakikada 180 istek, 24 başarısız oturum denemesi, veritabanı dışa aktarma yolu çağrıldı. Bu istek engellensin mi?',
    promptEn: 'Anonymous guest user, no authentication, 180 requests/min, 24 failed login attempts, requested database export path. Should this be blocked?'
  },
  {
    id: 'cloud-routing',
    category: 'Cloud DevOps',
    categoryTr: 'Bulut & Mikroservis',
    icon: '⚡',
    title: 'Microservice Cluster Routing',
    titleTr: 'Mikroservis Küme Yönlendirme',
    prompt: 'Sistem yükü 45 ms gecikme, paket boyutu 14 KB, kullanıcı rolü "member". Bu paket doğrudan üretim (prod), oran sınırlayıcı (rate-limiter) veya inceleme (sandbox) kümelerinden hangisine yönlendirilmeli?',
    promptEn: 'System latency 45ms, payload size 14 KB, user role "member". Which cluster should this be routed to: direct production, rate-limiter queue, or sandbox audit?'
  },
  {
    id: 'fraud-triage',
    category: 'Fintech',
    categoryTr: 'Finansal Triage',
    icon: '💳',
    title: 'High-Velocity Card Payment',
    titleTr: 'Yüksek Hızlı Şüpheli Ödeme',
    prompt: 'İşlem tutarı 4500 USD, coğrafi konum değişimi son 10 dakikada 3 farklı ülke, kullanıcı ilk kez harcama yapıyor. Tehdit şiddeti derecesi (risk score) nedir?',
    promptEn: 'Transaction amount 4500 USD, 3 different countries within 10 minutes, first-time spender. What is the perceived threat severity score?'
  },
  {
    id: 'robotics-thermal',
    category: 'IoT & Robotics',
    categoryTr: 'Otonom Robotik',
    icon: '🤖',
    title: 'Autonomous Motor Thermal Safety',
    titleTr: 'Robotik Motor Sıcaklık Emniyeti',
    prompt: 'Endüstriyel robot kolu eklem sıcaklığı 82°C, motor torku %94, titreşim ivmesi normalin 2.8 katı. Acil soğutma ve durdurma protokolü devreye alınsın mı?',
    promptEn: 'Industrial robotic arm joint temp 82C, torque 94%, vibration 2.8x baseline. Should emergency thermal shutdown protocol be engaged?'
  }
];

if (typeof window !== 'undefined') {
  window.SCENARIO_PRESETS = SCENARIO_PRESETS;
}
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { SCENARIO_PRESETS };
}
