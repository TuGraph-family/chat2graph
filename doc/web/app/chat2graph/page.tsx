import { redirect } from 'next/navigation';
import { defaultLanguage } from '@/lib/i18n';

export default function ChatGraphPage() {
  redirect(`/chat2graph/${defaultLanguage}/principle/overview`);
}