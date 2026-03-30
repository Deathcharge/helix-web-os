'use client';

import { MarketplaceLayout } from '@/components/layouts/MarketplaceLayout';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { emailClientAPI, type EmailMessage } from '@/lib/web-os-api';
import {
  Archive,
  Inbox,
  Mail,
  Plus,
  RefreshCw,
  Search,
  Send,
  Sparkles,
  Star,
  Tag,
  Trash2,
} from 'lucide-react';
import Link from 'next/link';
import { logger } from '@/lib/logger';
import { useEffect, useState } from 'react';

type Email = {
  id: string;
  from: string;
  subject: string;
  preview: string;
  body: string;
  timestamp: Date;
  isRead: boolean;
  isStarred: boolean;
  category: 'primary' | 'social' | 'promotions' | 'spam';
  aiSummary?: string;
};

export default function EmailClientPage() {
  // API state
  const [emails, setEmails] = useState<EmailMessage[]>([]);
  const [selectedEmail, setSelectedEmail] = useState<EmailMessage | null>(null);
  const [filter, setFilter] = useState<'all' | 'primary' | 'social' | 'promotions' | 'starred'>(
    'all'
  );
  const [searchQuery, setSearchQuery] = useState('');
  const [isComposing, setIsComposing] = useState(false);
  const [composeDraft, setComposeDraft] = useState({
    to: '',
    subject: '',
    body: '',
    accountId: '0',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load emails on mount
  useEffect(() => {
    loadEmails();
  }, [filter]);

  const loadEmails = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const category = filter !== 'all' && filter !== 'starred' ? filter : undefined;
      const loadedEmails = await emailClientAPI.listMessages(undefined, category);
      setEmails(loadedEmails);
      if (loadedEmails.length > 0 && !selectedEmail) {
        setSelectedEmail(loadedEmails[0]);
      }
    } catch (err) {
      logger.warn('Email list load failed:', err);
      setEmails([]);
      setError('Unable to load emails — check your connection or log in');
    } finally {
      setIsLoading(false);
    }
  };

  const refreshEmails = async () => {
    setIsRefreshing(true);
    await loadEmails();
    setIsRefreshing(false);
  };

  const filteredEmails = emails.filter((email) => {
    if (filter === 'starred') return email.is_starred;
    if (filter !== 'all' && email.category !== filter) return false;
    if (
      searchQuery &&
      !email.subject.toLowerCase().includes(searchQuery.toLowerCase()) &&
      !email.from_address.toLowerCase().includes(searchQuery.toLowerCase())
    ) {
      return false;
    }
    return true;
  });

  const markAsRead = async (emailId: string) => {
    // Mark as read locally immediately for UX
    setEmails(emails.map((e) => (e.id === emailId ? { ...e, is_read: true } : e)));
    // Sync read status to backend (fire-and-forget)
    emailClientAPI.getMessage(emailId).catch((err) => {
      logger.warn('Email read sync failed:', err);
    });
  };

  const toggleStar = async (emailId: string) => {
    try {
      const updated = await emailClientAPI.toggleStar(emailId);
      setEmails(emails.map((e) => (e.id === emailId ? updated : e)));
      if (selectedEmail?.id === emailId) {
        setSelectedEmail(updated);
      }
    } catch (err) {
      // Fallback to local toggle
      setEmails(emails.map((e) => (e.id === emailId ? { ...e, is_starred: !e.is_starred } : e)));
    }
  };

  const deleteEmail = async (emailId: string) => {
    try {
      await emailClientAPI.deleteMessage(emailId);
      setEmails(emails.filter((e) => e.id !== emailId));
      if (selectedEmail?.id === emailId) {
        setSelectedEmail(null);
      }
    } catch (err) {
      logger.warn('Email deletion API failed, removing locally:', err);
      // Fallback to local delete
      setEmails(emails.filter((e) => e.id !== emailId));
    }
  };

  const sendEmail = async () => {
    try {
      setIsLoading(true);
      await emailClientAPI.composeEmail({
        account_id: composeDraft.accountId || '1',
        to: composeDraft.to,
        subject: composeDraft.subject,
        body: composeDraft.body,
      });
      setIsComposing(false);
      setComposeDraft({ to: '', subject: '', body: '', accountId: '0' });
      await refreshEmails();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send email');
    } finally {
      setIsLoading(false);
    }
  };

  const aiCompose = async () => {
    const prompt = composeDraft.subject
      ? `Write a professional email reply about: ${composeDraft.subject}. Keep it concise (2-3 sentences).`
      : 'Write a short professional email. Keep it concise (2-3 sentences).';

    try {
      setIsLoading(true);
      const res = await fetch('/api/copilot/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ message: prompt, agent: 'aria' }),
      });
      if (res.ok) {
        const data = await res.json();
        const reply = data.response || data.message || data.content || '';
        if (reply) {
          setComposeDraft({ ...composeDraft, body: reply });
          return;
        }
      }
    } catch (e) {
      logger.warn('Failed to get AI email reply', e);
    } finally {
      setIsLoading(false);
    }

    // API unavailable — inform user instead of showing random canned text
    setComposeDraft({
      ...composeDraft,
      body: '[AI compose unavailable — please write your reply manually]',
    });
  };

  const getAISummary = async (emailId: string) => {
    try {
      setIsLoading(true);
      const result = await emailClientAPI.getAISummary(emailId);
      setEmails(
        emails.map((e) =>
          e.id === emailId
            ? {
                ...e,
                ai_summary:
                  result.summary +
                  '\n\nKey Points: ' +
                  result.key_points.join(', ') +
                  '\nActions: ' +
                  result.action_items.join(', '),
              }
            : e
        )
      );
    } catch (err) {
      // AI summary is optional — log but don't block the UI
      logger.warn('AI email summary unavailable:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <MarketplaceLayout>
      <div className="min-h-screen bg-gradient-to-b from-background via-blue-950 to-background">
        <div className="container mx-auto px-4 py-8">
          {/* Header */}
          <div className="mb-6">
            <Link
              href="/marketplace/web-os"
              className="text-ucf-harmony hover:text-ucf-harmony/80 mb-4 inline-block"
            >
              ← Back to Web OS
            </Link>
            <h1 className="font-heading text-4xl font-bold mb-2 text-foreground">📧 Email Client</h1>
            <p className="text-muted-foreground">AI-powered email with smart filters</p>
          </div>

          {/* Email Interface */}
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
            {/* Sidebar */}
            <Card className="lg:col-span-1 bg-card/50 backdrop-blur-sm border-border p-4">
              <Button
                className="w-full mb-4 bg-blue-600 hover:bg-blue-700"
                onClick={() => setIsComposing(true)}
              >
                <Plus className="h-4 w-4 mr-2" />
                Compose
              </Button>

              <div className="space-y-1">
                <Button
                  variant={filter === 'all' ? 'default' : 'ghost'}
                  className="w-full justify-start"
                  onClick={() => setFilter('all')}
                >
                  <Inbox className="h-4 w-4 mr-2" />
                  All Mail ({emails.length})
                </Button>
                <Button
                  variant={filter === 'primary' ? 'default' : 'ghost'}
                  className="w-full justify-start"
                  onClick={() => setFilter('primary')}
                >
                  <Mail className="h-4 w-4 mr-2" />
                  Primary ({emails.filter((e) => e.category === 'primary').length})
                </Button>
                <Button
                  variant={filter === 'social' ? 'default' : 'ghost'}
                  className="w-full justify-start"
                  onClick={() => setFilter('social')}
                >
                  <Tag className="h-4 w-4 mr-2" />
                  Social ({emails.filter((e) => e.category === 'social').length})
                </Button>
                <Button
                  variant={filter === 'promotions' ? 'default' : 'ghost'}
                  className="w-full justify-start"
                  onClick={() => setFilter('promotions')}
                >
                  <Tag className="h-4 w-4 mr-2" />
                  Promotions ({emails.filter((e) => e.category === 'promotions').length})
                </Button>
                <Button
                  variant={filter === 'starred' ? 'default' : 'ghost'}
                  className="w-full justify-start"
                  onClick={() => setFilter('starred')}
                >
                  <Star className="h-4 w-4 mr-2" />
                  Starred ({emails.filter((e) => e.is_starred).length})
                </Button>
              </div>

              <div className="mt-6 pt-6 border-t border-border">
                {error && (
                  <Card className="mb-3 p-2 bg-red-500/10 border-red-500/30">
                    <p className="text-xs text-red-200">{error}</p>
                  </Card>
                )}
                <Button
                  variant="outline"
                  className="w-full mb-2"
                  onClick={refreshEmails}
                  disabled={isRefreshing}
                >
                  <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
                  {isRefreshing ? 'Refreshing...' : 'Refresh'}
                </Button>
              </div>
            </Card>

            {/* Email List */}
            {!isComposing && (
              <>
                <Card className="lg:col-span-1 bg-card/50 backdrop-blur-sm border-border p-4 max-h-[600px] overflow-y-auto">
                  <div className="mb-4">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <input
                        type="text"
                        placeholder="Search emails..."
                        className="w-full pl-10 pr-4 py-2 bg-background border border-border rounded-lg text-sm"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    {filteredEmails.map((email) => (
                      <div
                        key={email.id}
                        className={`p-3 rounded-lg cursor-pointer transition-colors ${
                          selectedEmail?.id === email.id
                            ? 'bg-blue-500/20 border border-blue-500/50'
                            : 'bg-card hover:bg-card/80 border border-transparent'
                        }`}
                        onClick={() => {
                          setSelectedEmail(email);
                          markAsRead(email.id);
                        }}
                      >
                        <div className="flex items-start justify-between mb-1">
                          <span
                            className={`text-sm font-medium ${
                              !email.is_read ? 'text-foreground' : 'text-muted-foreground'
                            }`}
                          >
                            {email.from_address}
                          </span>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              toggleStar(email.id);
                            }}
                          >
                            <Star
                              className={`h-4 w-4 ${
                                email.is_starred
                                  ? 'fill-yellow-400 text-yellow-400'
                                  : 'text-muted-foreground'
                              }`}
                            />
                          </button>
                        </div>
                        <div
                          className={`text-sm mb-1 ${
                            !email.is_read
                              ? 'font-semibold text-foreground'
                              : 'text-muted-foreground'
                          }`}
                        >
                          {email.subject}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {email.body_text.slice(0, 100)}...
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                          {new Date(email.received_at).toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>

                {/* Email Content */}
                <Card className="lg:col-span-2 bg-card/50 backdrop-blur-sm border-border p-6">
                  {selectedEmail ? (
                    <>
                      <div className="flex items-start justify-between mb-6">
                        <div>
                          <h2 className="font-heading text-2xl font-bold text-foreground mb-2">
                            {selectedEmail.subject}
                          </h2>
                          <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <span>From: {selectedEmail.from_address}</span>
                            <span>•</span>
                            <span>{new Date(selectedEmail.received_at).toLocaleString()}</span>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => toggleStar(selectedEmail.id)}
                          >
                            <Star
                              className={`h-4 w-4 ${
                                selectedEmail.is_starred ? 'fill-yellow-400 text-yellow-400' : ''
                              }`}
                            />
                          </Button>
                          <Button variant="ghost" size="sm">
                            <Archive className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => deleteEmail(selectedEmail.id)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>

                      <div className="prose prose-invert max-w-none mb-6">
                        <p className="text-foreground whitespace-pre-wrap">
                          {selectedEmail.body_text}
                        </p>
                      </div>

                      {selectedEmail.ai_summary && (
                        <Card className="p-4 bg-purple-500/10 border-purple-500/30 mb-4">
                          <h3 className="text-sm font-semibold text-purple-200 mb-2 flex items-center gap-2">
                            <Sparkles className="h-4 w-4" />
                            AI Summary
                          </h3>
                          <p className="text-sm text-purple-100">{selectedEmail.ai_summary}</p>
                        </Card>
                      )}

                      <div className="flex gap-2">
                        <Button
                          className="bg-blue-600 hover:bg-blue-700"
                          onClick={() => getAISummary(selectedEmail.id)}
                          disabled={isLoading}
                        >
                          <Sparkles className="h-4 w-4 mr-2" />
                          {isLoading ? 'Generating...' : 'AI Summarize'}
                        </Button>
                        <Button variant="outline">Reply</Button>
                        <Button variant="outline">Forward</Button>
                      </div>
                    </>
                  ) : (
                    <div className="flex items-center justify-center h-full text-muted-foreground">
                      <div className="text-center">
                        <Mail className="h-12 w-12 mx-auto mb-4 opacity-50" />
                        <p>Select an email to read</p>
                      </div>
                    </div>
                  )}
                </Card>
              </>
            )}

            {/* Compose Email */}
            {isComposing && (
              <Card className="lg:col-span-3 bg-card/50 backdrop-blur-sm border-border p-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="font-heading text-2xl font-bold text-foreground">New Message</h2>
                  <Button variant="ghost" onClick={() => setIsComposing(false)}>
                    ✕
                  </Button>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="text-sm text-muted-foreground mb-1 block">To</label>
                    <input
                      type="email"
                      className="w-full px-4 py-2 bg-background border border-border rounded-lg"
                      placeholder="recipient@example.com"
                      value={composeDraft.to}
                      onChange={(e) => setComposeDraft({ ...composeDraft, to: e.target.value })}
                    />
                  </div>

                  <div>
                    <label className="text-sm text-muted-foreground mb-1 block">Subject</label>
                    <input
                      type="text"
                      className="w-full px-4 py-2 bg-background border border-border rounded-lg"
                      placeholder="Email subject"
                      value={composeDraft.subject}
                      onChange={(e) =>
                        setComposeDraft({
                          ...composeDraft,
                          subject: e.target.value,
                        })
                      }
                    />
                  </div>

                  <div>
                    <label className="text-sm text-muted-foreground mb-1 block">Message</label>
                    <textarea
                      className="w-full px-4 py-2 bg-background border border-border rounded-lg min-h-[300px]"
                      placeholder="Write your message..."
                      value={composeDraft.body}
                      onChange={(e) =>
                        setComposeDraft({
                          ...composeDraft,
                          body: e.target.value,
                        })
                      }
                    />
                  </div>

                  <div className="flex gap-2">
                    <Button
                      className="bg-blue-600 hover:bg-blue-700"
                      onClick={sendEmail}
                      disabled={isLoading}
                    >
                      <Send className="h-4 w-4 mr-2" />
                      {isLoading ? 'Sending...' : 'Send'}
                    </Button>
                    <Button variant="outline" onClick={aiCompose}>
                      <Sparkles className="h-4 w-4 mr-2" />
                      AI Compose
                    </Button>
                    <Button variant="ghost" onClick={() => setIsComposing(false)}>
                      Cancel
                    </Button>
                  </div>
                </div>
              </Card>
            )}
          </div>
        </div>
      </div>
    </MarketplaceLayout>
  );
}
