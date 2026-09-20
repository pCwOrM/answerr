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
    promptEn: 'User role "admin", authenticated=true, request frequency 1.5 req/s, 0 failed attempts. Should execution be permitted?',
    state: {
      user_role: 'admin',
      auth_status: true,
      req_frequency_sec: 1.5,
      failed_attempts: 0
    },
    question: {
      key: 'allow_execution',
      type: 'noul',
      instructionsTr: 'Bu operasyonun yürütülmesine onay verilsin mi?',
      instructionsEn: 'Should execution be permitted?',
      threshold: 0.5
    },
    interpretation: {
      tr: {
        trueVerdict: 'ONAYLANDI (TRUE)',
        falseVerdict: 'REDDEDİLDİ (FALSE)',
        trueAction: 'Yönetici kimliği ve oturum geçerliliği doğrulandı. İşlem derhal üretim boru hattında yürütülüyor.',
        falseAction: 'Yetkilendirme kriterleri sağlanamadı. Operasyon durduruldu.'
      },
      en: {
        trueVerdict: 'APPROVED (TRUE)',
        falseVerdict: 'DENIED (FALSE)',
        trueAction: 'Admin credentials and session parameters verified. Request executed immediately in production pipeline.',
        falseAction: 'Authorization criteria not met. Operation aborted.'
      }
    }
  },
  {
    id: 'api-security-attack',
    category: 'Cybersecurity',
    categoryTr: 'Siber Güvenlik',
    icon: '🚨',
    title: 'DDoS Burst from Anonymous IP',
    titleTr: 'Anonim IP Şüpheli DDoS Trafiği',
    prompt: 'Anonim konuk (guest) kullanıcı, doğrulama yok, son 1 dakikada 180 istek, 24 başarısız oturum denemesi, veritabanı dışa aktarma yolu çağrıldı. Bu istek engellensin mi?',
    promptEn: 'Anonymous guest user, no authentication, 180 requests/min, 24 failed login attempts, requested database export path. Should this be blocked?',
    state: {
      user_role: 'guest',
      auth_status: false,
      req_count_1m: 180,
      failed_logins: 24,
      target_endpoint: '/api/v1/db/export'
    },
    question: {
      key: 'block_request',
      type: 'noul',
      instructionsTr: 'Bu istek engellensin mi?',
      instructionsEn: 'Should this request be blocked?',
      threshold: 0.5
    },
    interpretation: {
      tr: {
        trueVerdict: 'ENGELLEME ONAYLANDI (TRUE)',
        falseVerdict: 'GEÇİŞE İZİN VERİLDİ (FALSE)',
        trueAction: 'Şüpheli DDoS ve kaba kuvvet (brute-force) aktivitesi tespit edildi. İstek derhal engellendi ve kaynak IP karantinaya alındı.',
        falseAction: 'İstek güvenlik sınırları içinde değerlendirildi; geçişe izin verildi.'
      },
      en: {
        trueVerdict: 'BLOCK APPROVED (TRUE)',
        falseVerdict: 'ALLOW PASS (FALSE)',
        trueAction: 'Suspicious DDoS burst and brute-force activity detected. Request blocked immediately and source IP quarantined.',
        falseAction: 'Request evaluated within safe thresholds; traffic allowed to pass.'
      }
    }
  },
  {
    id: 'cloud-routing',
    category: 'Cloud DevOps',
    categoryTr: 'Bulut & Mikroservis',
    icon: '⚡',
    title: 'Microservice Cluster Routing',
    titleTr: 'Mikroservis Küme Yönlendirme',
    prompt: 'Sistem yükü 45 ms gecikme, paket boyutu 14 KB, kullanıcı rolü "member". Bu paket doğrudan üretim (prod), oran sınırlayıcı (rate-limiter) veya inceleme (sandbox) kümelerinden hangisine yönlendirilmeli?',
    promptEn: 'System latency 45ms, payload size 14 KB, user role "member". Which cluster should this be routed to: direct production, rate-limiter queue, or sandbox audit?',
    state: {
      latency_ms: 45,
      payload_kb: 14,
      user_role: 'member'
    },
    question: {
      key: 'cluster_route',
      type: 'choice',
      instructionsTr: 'Bu paket doğrudan üretim (prod), oran sınırlayıcı (rate-limiter) veya inceleme (sandbox) kümelerinden hangisine yönlendirilmeli?',
      instructionsEn: 'Which cluster should this packet be routed to: direct production, rate-limiter queue, or sandbox audit?',
      criteriaTr: {
        prod: 'Doğrudan Üretim Kümesi (Production)',
        rate_limiter: 'Oran Sınırlama Kuyruğu (Rate-Limiter)',
        sandbox: 'Yalıtılmış Güvenlik İncelemesi (Sandbox)'
      },
      criteriaEn: {
        prod: 'Direct Production API',
        rate_limiter: 'Rate-Limiting Buffer Queue',
        sandbox: 'Isolated Sandbox Audit'
      }
    },
    interpretation: {
      tr: {
        actionPrefix: 'Trafik akışı Sistem-1 fraktal kuadran faz kilitlenmesiyle yönlendirildi: '
      },
      en: {
        actionPrefix: 'Traffic stream routed via System-1 fractal quadrant phase-lock: '
      }
    }
  },
  {
    id: 'fraud-triage',
    category: 'Fintech',
    categoryTr: 'Finansal Triage',
    icon: '💳',
    title: 'High-Velocity Card Payment',
    titleTr: 'Yüksek Hızlı Şüpheli Ödeme',
    prompt: 'İşlem tutarı 4500 USD, coğrafi konum değişimi son 10 dakikada 3 farklı ülke, kullanıcı ilk kez harcama yapıyor. Tehdit şiddeti derecesi (risk score) nedir?',
    promptEn: 'Transaction amount 4500 USD, 3 different countries within 10 minutes, first-time spender. What is the perceived threat severity score?',
    state: {
      amount_usd: 4500,
      geo_countries_10m: 3,
      first_time_user: true
    },
    question: {
      key: 'fraud_risk_score',
      type: 'score',
      instructionsTr: 'Tehdit şiddeti derecesi (risk score) nedir?',
      instructionsEn: 'What is the perceived threat severity score?',
      criteriaTr: ['Normal / Güvenli', 'Düşük Anomali', 'Yüksek Risk', 'Kritik Tehdit / Bloke'],
      criteriaEn: ['Normal / Benign', 'Minor Anomaly', 'Elevated Risk', 'Critical Threat / Block']
    },
    interpretation: {
      tr: {
        actionPrefix: 'Finansal risk derecelendirmesi kaydedildi. Yüksek ve kritik risk seviyeleri için 3D-Secure ve kart provizyon blokesi uygulandı.'
      },
      en: {
        actionPrefix: 'Financial risk rating recorded. 3D-Secure challenge and authorization hold applied for elevated risks.'
      }
    }
  },
  {
    id: 'robotics-thermal',
    category: 'IoT & Robotics',
    categoryTr: 'Otonom Robotik',
    icon: '🤖',
    title: 'Autonomous Motor Thermal Safety',
    titleTr: 'Robotik Motor Sıcaklık Emniyeti',
    prompt: 'Endüstriyel robot kolu eklem sıcaklığı 82°C, motor torku %94, titreşim ivmesi normalin 2.8 katı. Acil soğutma ve durdurma protokolü devreye alınsın mı?',
    promptEn: 'Industrial robotic arm joint temp 82C, torque 94%, vibration 2.8x baseline. Should emergency thermal shutdown protocol be engaged?',
    state: {
      joint_temp_c: 82,
      motor_torque_pct: 94,
      vibration_multiplier: 2.8
    },
    question: {
      key: 'emergency_shutdown',
      type: 'noul',
      instructionsTr: 'Acil soğutma ve durdurma protokolü devreye alınsın mı?',
      instructionsEn: 'Should emergency thermal shutdown protocol be engaged?',
      threshold: 0.5
    },
    interpretation: {
      tr: {
        trueVerdict: 'ACİL DURDURMA DEVREYE ALINDI (TRUE)',
        falseVerdict: 'NORMAL ÇALIŞMA (FALSE)',
        trueAction: 'Kritik termal ve mekanik aşım (82°C / %94 tork) algılandı! Acil soğutma valfleri açıldı, servo frenler kilitlendi ve durdurma protokolü yürütüldü.',
        falseAction: 'Sensör verileri tolerans aralığında; acil müdahale gerekmiyor, robot çalışma döngüsüne devam ediyor.'
      },
      en: {
        trueVerdict: 'EMERGENCY SHUTDOWN ENGAGED (TRUE)',
        falseVerdict: 'NORMAL OPERATION (FALSE)',
        trueAction: 'Critical thermal and mechanical overload (82°C / 94% torque) detected! Emergency cooling valves opened, servo brakes locked, shutdown protocol executed.',
        falseAction: 'Sensor readings within tolerance; no emergency action required, robot arm continues standard cycle.'
      }
    }
  },
  {
    id: 'game-ai-combat',
    category: 'Game AI',
    categoryTr: 'Oyun Yapay Zekası',
    icon: '🎯',
    title: 'NPC Tactical Combat Reflex',
    titleTr: 'NPC Taktik Savaş Refleksi',
    prompt: 'NPC sağlık durumu %22, kalan mühimmat %14, düşman mesafesi 6 metre ve doğrudan ateş altında. Agresif taarruza devam edilsin mi, yoksa taktiksel geri çekilip siper mi alınsın?',
    promptEn: 'NPC unit health 22%, ammo 14%, enemy distance 6m under heavy fire. Should aggressive assault continue, or execute tactical retreat to cover?',
    state: {
      health_pct: 22,
      ammo_pct: 14,
      enemy_distance_m: 6,
      under_fire: true,
      cover_available: true
    },
    question: {
      key: 'continue_assault',
      type: 'noul',
      instructionsTr: 'Agresif taarruza devam edilsin mi?',
      instructionsEn: 'Should aggressive assault continue?',
      threshold: 0.5
    },
    interpretation: {
      tr: {
        trueVerdict: 'SALDIRIYA DEVAM ET (TRUE)',
        falseVerdict: 'SİPERE GEÇ / GERİ ÇEKİL (FALSE)',
        trueAction: 'Savaş parametreleri taarruz için yeterli görüldü; birim saldırı pozisyonunu koruyor.',
        falseAction: 'Kritik düşük sağlık (%22) ve mühimmat (%14) tespit edildi! Fraktal omurilik refleksi birimi derhal en yakın korunaklı siper arkasına çekti.'
      },
      en: {
        trueVerdict: 'CONTINUE ASSAULT (TRUE)',
        falseVerdict: 'TACTICAL RETREAT TO COVER (FALSE)',
        trueAction: 'Combat parameters deemed sufficient for offensive posture; unit maintains attack vector.',
        falseAction: 'Critical low health (22%) and depleted ammo (14%) detected! Fractal spinal reflex executes immediate dash to nearest defensive cover.'
      }
    }
  }
];

if (typeof window !== 'undefined') {
  window.SCENARIO_PRESETS = SCENARIO_PRESETS;
}
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { SCENARIO_PRESETS };
}
