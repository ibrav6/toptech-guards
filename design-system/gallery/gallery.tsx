import { CreateProject } from '../src/stories/examples';
import * as React from 'react';
import { ArrowUpLeft, Blocks, CircleHelp, Compass, Moon, Palette, PanelRight, Sun } from 'lucide-react';
import { AppShell, BrandMark, Button, StatusBadge, ThemeProvider, type DesignDirection, type DesignTheme } from '@toptech/ui';

const sections = [
  { href: '#overview', label: 'نظرة على الهوية', icon: <Compass size={19}/> },
  { href: '#foundations', label: 'الأسس البصرية', icon: <Palette size={19}/> },
  { href: '#components', label: 'المكوّنات', icon: <Blocks size={19}/> },
  { href: '#patterns', label: 'قوالب المنتجات', icon: <PanelRight size={19}/> },
  { href: '#guidelines', label: 'دليل الاستخدام', icon: <CircleHelp size={19}/> }
];
import { Block } from './shared';
const Foundations = React.lazy(() => import('./sections').then(m => ({ default: m.Foundations })));
const Components = React.lazy(() => import('./sections').then(m => ({ default: m.Components })));
const Patterns = React.lazy(() => import('./sections').then(m => ({ default: m.Patterns })));
const Guidelines = React.lazy(() => import('./sections').then(m => ({ default: m.Guidelines })));
export function Overview({ navigate }: { navigate: (href: string) => void }) {
  return <><section className="g-hero"><div className="g-hero-copy"><span className="g-eyebrow"><span className="g-live-dot"/>نظام هوية قمم التقنية · الإصدار الأول</span><h1>وضوحٌ يقود<br/>العمل<span className="g-blue">.</span></h1><p>لغة واحدة لمنتجاتنا.<br/>مساحة للتركيز، وتفاصيل تستحق الثقة.</p><div className="g-hero-actions"><Button onClick={() => navigate('#components')}>استكشف المكوّنات<ArrowUpLeft className="ltr:rotate-90"/></Button><Button variant="ghost" onClick={() => navigate('#guidelines')}>دليل البناء</Button></div><div className="g-hero-meta"><span>عربية أولًا</span><i/><span>فاتح وداكن</span><i/><span>من الجوال إلى المكتب</span></div></div><div className="g-signature" aria-label="نموذج العلامة"><div className="g-signature-grid"/><div className="g-signature-top"><span lang="en" dir="ltr">TOPTECH / DESIGN</span><span>01</span></div><BrandMark width={116} height={116}/><div className="g-signature-bottom"><span>قمم التقنية</span><small>أدوات ذكية. عمل واضح.</small></div></div></section>
  <div className="g-principles"><article><span>01</span><h2>القرار في المقدّمة</h2><p>إجراء رئيسي واضح، وما يدعمه قريب منه.</p></article><article><span>02</span><h2>اللون له وظيفة</h2><p>محايد للمساحة، أزرق للفعل، ودلالات للحالة.</p></article><article><span>03</span><h2>الثبات يصنع الثقة</h2><p>السلوك نفسه أينما انتقلت داخل المنتج.</p></article></div>
  <div className="g-overview-grid"><Block title="لغة اللون" note="دفءٌ محسوب"><div className="g-palette"><div style={{background:'#FAF9F5',color:'#2B2A27'}}><span>مساحة</span><small>#FAF9F5</small></div><div style={{background:'#2B2A27',color:'#FAF9F5'}}><span>حبر</span><small>#2B2A27</small></div><div style={{background:'hsl(225 80% 49%)',color:'#fff'}}><span>فعل</span><small>أزرق قمم</small></div><div style={{background:'#E6E4DB',color:'#2B2A27'}}><span>حدود</span><small>#E6E4DB</small></div></div></Block><Block title="صوتٌ واضح" note="IBM Plex Sans Arabic"><div className="g-type-specimen"><span className="g-type-aa">أبج<span>Aa</span></span><p>التقنية الجيّدة تجعل الخطوة التالية أوضح.</p><span className="g-type-digits">٠١٢٣٤٥٦٧٨٩ <bdi>0123456789</bdi></span></div></Block></div>
  <Block title="تفاصيل من النظام" note="مكوّنات حقيقية قابلة للتجربة"><div className="g-preview-row"><div><StatusBadge tone="success">جاهز للمراجعة</StatusBadge><h3>مساحة عمل للفريق</h3><p>كل ما تحتاجه للخطوة التالية.</p></div><CreateProject/></div></Block></>;
}
let initialSections: typeof import('./sections') | undefined;
// الصفحة المطلوبة تُجهّز قبل أول رسم؛ رسم فراغ ثم محتواها حرّك الذيل بـCLS0.54.
export async function prepareGallery(hash = window.location.hash) {
 if (['#foundations', '#components', '#patterns', '#guidelines'].includes(hash)) initialSections = await import('./sections');
}
export function Gallery({ initialHash, initialSearch }: { initialHash?: string; initialSearch?: string } = {}) {
 // الأزرار المخبوزة لا تقبل نقرة تضيع قبل ربط معالجات React.
 React.useEffect(() => { const root = document.getElementById('root'); if (root) root.inert = false; }, []);
 const FoundationsView = initialSections?.Foundations ?? Foundations;
 const ComponentsView = initialSections?.Components ?? Components;
 const PatternsView = initialSections?.Patterns ?? Patterns;
 const GuidelinesView = initialSections?.Guidelines ?? Guidelines;
 const params = new URLSearchParams(initialSearch ?? window.location.search);
 const [theme,setTheme] = React.useState<DesignTheme>(params.get('theme') === 'dark' ? 'dark': params.get('theme') === 'auto' ? 'auto' : 'light');
 const [dir,setDir] = React.useState<DesignDirection>(params.get('dir') === 'ltr' ? 'ltr':'rtl');
 const hash = initialHash ?? window.location.hash;
 const [active,setActive] = React.useState(sections.some(s=>s.href===hash) ? hash : '#overview');
 React.useEffect(()=>{ const sync=()=>setActive(sections.some(s=>s.href===window.location.hash) ? window.location.hash : '#overview'); window.addEventListener('hashchange',sync); return ()=>window.removeEventListener('hashchange',sync); },[]);
 function navigate(href:string){window.location.hash=href; setActive(href); window.scrollTo({top:0,behavior:'instant'});}
 return <ThemeProvider theme={theme} dir={dir}><AppShell items={sections} activeHref={active} onNavigate={navigate} header={<div className="g-header-tools"><span className="g-release">نظام التصميم <bdi>0.1</bdi></span><Button variant="ghost" size="icon" aria-label={theme==='light'?'تفعيل المظهر الداكن':'تفعيل المظهر الفاتح'} onClick={()=>setTheme(theme==='light'?'dark':'light')}>{theme==='light'?<Moon/>:<Sun/>}</Button><Button variant="outline" className="g-dir-button" aria-label="تبديل اتجاه الواجهة" onClick={()=>setDir(dir==='rtl'?'ltr':'rtl')}>{dir==='rtl'?'LTR':'RTL'}</Button></div>}><div className="g-container"><React.Suspense fallback={<div aria-busy="true" style={{ minHeight: '80vh' }} />}>{active==='#overview'?<Overview navigate={navigate}/>:active==='#foundations'?<FoundationsView/>:active==='#components'?<ComponentsView/>:active==='#patterns'?<PatternsView/>:<GuidelinesView/>}</React.Suspense><footer className="g-footer"><span>قمم التقنية</span><span>مرجع حيّ لبناء منتجاتنا</span><bdi>DESIGN / 01</bdi></footer></div></AppShell></ThemeProvider>;
}
