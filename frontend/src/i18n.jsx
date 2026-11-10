import { createContext, useContext, useEffect, useState } from "react";

// Customer-facing screens only (English, Hindi, Bengali). Staff screens stay in English.
const T = {
  en: {
    "nav.home": "Home", "nav.refills": "Refills", "nav.orders": "My orders", "nav.messages": "Messages", "nav.signOut": "Sign out",
    "login.tagline": "Refill your regular medicines in a minute.", "login.mobile": "Mobile number", "login.send": "Send code",
    "login.heroEyebrow": "Your pharmacy, connected", "login.heroTitle": "A simpler way to stay on top of your health.",
    "login.heroCopy": "Order medicines for you and your family, with a pharmacist checking every prescription.",
    "login.heroStep1": "Upload with confidence", "login.heroStep1Copy": "AI helps read your prescription.",
    "login.heroStep2": "Reviewed by a pharmacist", "login.heroStep2Copy": "A human verifies medicines and dosage.",
    "login.heroStep3": "Never miss a refill", "login.heroStep3Copy": "Timely reminders for ongoing care.",
    "login.heroFooter": "Secure prescriptions. Thoughtful care.",
    "login.phoneHelper": "We’ll send a one-time code to your mobile number.",
    "login.termsNote": "By continuing, you agree to our Terms of service and Privacy policy.",
    "login.sentTo": "We sent a 6-digit code to", "login.code": "Code", "login.signIn": "Sign in", "login.other": "Use a different number",
    "login.createAccount": "Create account", "login.name": "Full name", "login.register": "Create account",
    "login.haveAccount": "Already have an account?", "login.returnLogin": "Return to sign in",
    "home.hello": "Hello, {name}", "home.orderingFor": "Ordering for", "home.lastOrder": "Your last order", "home.reorder": "Reorder",
    "home.checkNote": "A pharmacist checks every order before it is sent.", "home.startFirst": "Start your first refill",
    "home.startFirstSub": "Upload a photo of your prescription. We will read it and a pharmacist will check it.",
    "home.uploadRx": "Upload prescription", "home.uploadNew": "Upload a new prescription", "home.search": "Search medicines", "home.recent": "Recent orders",
    "upload.title": "Upload your prescription", "upload.sub": "Take a clear photo of the whole page. Only our pharmacists can see it.",
    "upload.photo": "Photo of prescription", "upload.continue": "Continue", "upload.reading": "Reading your prescription…",
    "cart.title": "Your order", "cart.sub": "Check the medicines and quantities. A pharmacist verifies everything before it is sent.",
    "cart.packs": "Packs", "cart.payment": "Payment", "cart.cod": "Pay on delivery", "cart.upi": "UPI (test mode)",
    "cart.total": "Estimated total", "cart.place": "Place order",
  },
  hi: {
    "nav.home": "होम", "nav.refills": "रिफ़िल", "nav.orders": "मेरे ऑर्डर", "nav.messages": "संदेश", "nav.signOut": "साइन आउट",
    "login.tagline": "अपनी नियमित दवाइयाँ एक मिनट में दोबारा मँगाएँ।", "login.mobile": "मोबाइल नंबर", "login.send": "कोड भेजें",
    "login.heroEyebrow": "आपकी फ़ार्मेसी, अब साथ",
    "login.heroTitle": "अपनी सेहत का ध्यान रखना अब और आसान।",
    "login.heroCopy": "अपने और परिवार के लिए दवाइयाँ मँगाएँ। हर पर्चे की जाँच फ़ार्मासिस्ट करेगा।",
    "login.heroStep1": "निश्चिंत होकर अपलोड करें", "login.heroStep1Copy": "AI आपके पर्चे को पढ़ने में मदद करता है।",
    "login.heroStep2": "फ़ार्मासिस्ट द्वारा जाँच", "login.heroStep2Copy": "एक विशेषज्ञ दवाइयों और खुराक की जाँच करता है।",
    "login.heroStep3": "रिफ़िल न भूलें", "login.heroStep3Copy": "नियमित दवाइयों के लिए समय पर याद दिलाएँ।",
    "login.heroFooter": "सुरक्षित पर्चे। सोच-समझकर देखभाल।",
    "login.phoneHelper": "हम आपके मोबाइल नंबर पर एक बार इस्तेमाल होने वाला कोड भेजेंगे।",
    "login.termsNote": "आगे बढ़ने पर, आप हमारी सेवा की शर्तों और गोपनीयता नीति से सहमत होते हैं।",
    "login.sentTo": "हमने 6 अंकों का कोड भेजा है:", "login.code": "कोड", "login.signIn": "साइन इन करें", "login.other": "दूसरा नंबर इस्तेमाल करें",
    "login.createAccount": "खाता बनाएँ", "login.name": "पूरा नाम", "login.register": "खाता बनाएँ",
    "login.haveAccount": "पहले से खाता है?", "login.returnLogin": "साइन इन पर लौटें",
    "home.hello": "नमस्ते, {name}", "home.orderingFor": "किसके लिए मँगा रहे हैं", "home.lastOrder": "आपका पिछला ऑर्डर", "home.reorder": "दोबारा ऑर्डर करें",
    "home.checkNote": "भेजने से पहले हर ऑर्डर की जाँच एक फ़ार्मासिस्ट करता है।", "home.startFirst": "अपना पहला रिफ़िल शुरू करें",
    "home.startFirstSub": "अपने पर्चे की फ़ोटो अपलोड करें। हम उसे पढ़ेंगे और फ़ार्मासिस्ट उसकी जाँच करेगा।",
    "home.uploadRx": "पर्चा अपलोड करें", "home.uploadNew": "नया पर्चा अपलोड करें", "home.search": "दवाइयाँ खोजें", "home.recent": "हाल के ऑर्डर",
    "upload.title": "अपना पर्चा अपलोड करें", "upload.sub": "पूरे पन्ने की साफ़ फ़ोटो लें। इसे केवल हमारे फ़ार्मासिस्ट देख सकते हैं।",
    "upload.photo": "पर्चे की फ़ोटो", "upload.continue": "आगे बढ़ें", "upload.reading": "आपका पर्चा पढ़ा जा रहा है…",
    "cart.title": "आपका ऑर्डर", "cart.sub": "दवाइयाँ और मात्रा जाँच लें। भेजने से पहले फ़ार्मासिस्ट सब कुछ जाँचता है।",
    "cart.packs": "पैक", "cart.payment": "भुगतान", "cart.cod": "डिलीवरी पर भुगतान", "cart.upi": "UPI (टेस्ट मोड)",
    "cart.total": "अनुमानित कुल", "cart.place": "ऑर्डर करें",
  },
  bn: {
    "nav.home": "হোম", "nav.refills": "রিফিল", "nav.orders": "আমার অর্ডার", "nav.messages": "বার্তা", "nav.signOut": "সাইন আউট",
    "login.tagline": "আপনার নিয়মিত ওষুধ এক মিনিটে আবার অর্ডার করুন।", "login.mobile": "মোবাইল নম্বর", "login.send": "কোড পাঠান",
    "login.heroEyebrow": "আপনার ফার্মেসি, এখন হাতের কাছে",
    "login.heroTitle": "স্বাস্থ্যের যত্ন নেওয়া এখন আরও সহজ।",
    "login.heroCopy": "আপনার ও পরিবারের জন্য ওষুধ অর্ডার করুন; প্রতিটি প্রেসক্রিপশন ফার্মাসিস্ট যাচাই করেন।",
    "login.heroStep1": "নিশ্চিন্তে আপলোড করুন", "login.heroStep1Copy": "AI আপনার প্রেসক্রিপশন পড়তে সাহায্য করে।",
    "login.heroStep2": "ফার্মাসিস্টের যাচাই", "login.heroStep2Copy": "একজন বিশেষজ্ঞ ওষুধ ও মাত্রা যাচাই করেন।",
    "login.heroStep3": "রিফিলের কথা ভুলবেন না", "login.heroStep3Copy": "নিয়মিত ওষুধের জন্য সময়মতো মনে করিয়ে দেওয়া হয়।",
    "login.heroFooter": "নিরাপদ প্রেসক্রিপশন। যত্নশীল পরিষেবা।",
    "login.phoneHelper": "আপনার মোবাইল নম্বরে একবার ব্যবহারযোগ্য কোড পাঠানো হবে।",
    "login.termsNote": "এগিয়ে গেলে, আপনি আমাদের পরিষেবার শর্তাবলি ও গোপনীয়তা নীতিতে সম্মত হচ্ছেন।",
    "login.sentTo": "আমরা ৬ সংখ্যার কোড পাঠিয়েছি:", "login.code": "কোড", "login.signIn": "সাইন ইন করুন", "login.other": "অন্য নম্বর ব্যবহার করুন",
    "login.createAccount": "অ্যাকাউন্ট তৈরি করুন", "login.name": "পুরো নাম", "login.register": "অ্যাকাউন্ট তৈরি করুন",
    "login.haveAccount": "আগে থেকেই অ্যাকাউন্ট আছে?", "login.returnLogin": "সাইন ইন-এ ফিরুন",
    "home.hello": "নমস্কার, {name}", "home.orderingFor": "কার জন্য অর্ডার করছেন", "home.lastOrder": "আপনার আগের অর্ডার", "home.reorder": "আবার অর্ডার করুন",
    "home.checkNote": "পাঠানোর আগে প্রতিটি অর্ডার একজন ফার্মাসিস্ট যাচাই করেন।", "home.startFirst": "আপনার প্রথম রিফিল শুরু করুন",
    "home.startFirstSub": "আপনার প্রেসক্রিপশনের ছবি আপলোড করুন। আমরা সেটি পড়ব এবং একজন ফার্মাসিস্ট যাচাই করবেন।",
    "home.uploadRx": "প্রেসক্রিপশন আপলোড করুন", "home.uploadNew": "নতুন প্রেসক্রিপশন আপলোড করুন", "home.search": "ওষুধ খুঁজুন", "home.recent": "সাম্প্রতিক অর্ডার",
    "upload.title": "আপনার প্রেসক্রিপশন আপলোড করুন", "upload.sub": "পুরো পাতার পরিষ্কার ছবি তুলুন। শুধু আমাদের ফার্মাসিস্টরা এটি দেখতে পাবেন।",
    "upload.photo": "প্রেসক্রিপশনের ছবি", "upload.continue": "এগিয়ে যান", "upload.reading": "আপনার প্রেসক্রিপশন পড়া হচ্ছে…",
    "cart.title": "আপনার অর্ডার", "cart.sub": "ওষুধ ও পরিমাণ দেখে নিন। পাঠানোর আগে ফার্মাসিস্ট সবকিছু যাচাই করেন।",
    "cart.packs": "প্যাক", "cart.payment": "পেমেন্ট", "cart.cod": "ডেলিভারির সময় পেমেন্ট", "cart.upi": "UPI (টেস্ট মোড)",
    "cart.total": "আনুমানিক মোট", "cart.place": "অর্ডার দিন",
  },
};
export const LANGS = [["en", "English"], ["hi", "हिन्दी"], ["bn", "বাংলা"]];

export function translate(lang, key, vars = {}) {
  const s = T[lang]?.[key] ?? T.en[key] ?? key;   // falls back to English, then to the key (staff labels are plain text)
  return s.replace(/\{(\w+)\}/g, (_, k) => vars[k] ?? "");
}

const Ctx = createContext(null);
export const useT = () => useContext(Ctx);

export function LangProvider({ children }) {
  const [lang, setLang] = useState(() => localStorage.getItem("medibridge.lang") || "en");
  useEffect(() => { localStorage.setItem("medibridge.lang", lang); document.documentElement.lang = lang; }, [lang]);
  return <Ctx.Provider value={{ lang, setLang, t: (k, v) => translate(lang, k, v) }}>{children}</Ctx.Provider>;
}

export function LangSwitch() {
  const { lang, setLang } = useT();
  return (
    <select aria-label="Language" value={lang} onChange={(e) => setLang(e.target.value)}
      style={{ width: "auto", minHeight: 36, padding: ".2rem .5rem", fontSize: ".9rem" }}>
      {LANGS.map(([c, n]) => <option key={c} value={c}>{n}</option>)}
    </select>
  );
}
