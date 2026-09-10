import * as React from 'react';
import type { Meta, StoryObj } from '@storybook/react-vite';
import { Home, Settings, Folder } from 'lucide-react';
import { AppShell, TextField } from '@toptech/ui';
import { TableExample } from './examples';
function ShellExample() {
 const [route,setRoute]=React.useState('/work');
 return <AppShell activeHref={route} onNavigate={setRoute} items={[{href:'/work',label:'مساحة العمل',icon:<Home size={18}/>},{href:'/work?tab=files',label:'الملفات',icon:<Folder size={18}/>},{href:'/settings',label:'الإعدادات',icon:<Settings size={18}/>}] }><div className="grid gap-6"><h1 className="text-3xl font-semibold">{route==='/settings'?'إعدادات الفريق':route.includes('?')?'ملفات الفريق':'مساحة العمل'}</h1>{route==='/settings'?<TextField label="اسم الفريق" defaultValue="فريق قمم"/>:<TableExample/>}</div></AppShell>;
}
const meta = { title:'القوالب/هيكل التطبيق', component: ShellExample, parameters:{ layout:'fullscreen' }, decorators:[Story=><div className="-m-8"><Story/></div>], tags:['autodocs'] } satisfies Meta<typeof ShellExample>;
export default meta;
export const Responsive: StoryObj<typeof meta> = { name:'تنقّل المكتب والجوال' };
