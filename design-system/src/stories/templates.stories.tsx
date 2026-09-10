import type { Meta, StoryObj } from '@storybook/react-vite';
import { Button, DetailPage, ListPage, PageHeader, PageSection, SettingsPage, StatusBadge, TextField } from '@toptech/ui';
import { FormExamples, NavigationExamples, TableExample } from './examples';
const meta = { title: 'القوالب/صفحات المنتج', tags: ['autodocs'] } satisfies Meta;
export default meta;
export const List: StoryObj = { name:'قائمة', render:()=><ListPage header={<PageHeader title="فرص الفريق" description="العمل الذي يحتاج اهتمام الفريق." actions={<Button>إضافة فرصة</Button>}/>} filters={<TextField label="البحث في الفرص" placeholder="اسم الفرصة"/>}><TableExample/></ListPage> };
export const Details: StoryObj = { name:'تفاصيل', render:()=><DetailPage header={<PageHeader eyebrow="فرص الفريق" title="تطوير منصة لخدمات المستفيدين" actions={<Button>متابعة الفرصة</Button>}/>} summary={<StatusBadge tone="success">جاهز للمراجعة</StatusBadge>} navigation={<NavigationExamples/>} aside={<PageSection title="الخطوة التالية"><p>راجع المتطلبات وحدد مسؤول المتابعة.</p></PageSection>}><PageSection title="ملخص الفرصة"><p>قالب يضع القرار قبل التفاصيل، ويجمع المعلومات المرتبطة في أقسام واضحة.</p></PageSection></DetailPage> };
export const Settings: StoryObj = { name:'إعدادات', render:()=><SettingsPage header={<PageHeader title="إعدادات مساحة العمل" description="معلومات الفريق وتفضيلات العمل."/>} footer={<><Button variant="outline">إلغاء</Button><Button>حفظ التغييرات</Button></>}><PageSection title="معلومات الفريق"><FormExamples/></PageSection></SettingsPage> };
