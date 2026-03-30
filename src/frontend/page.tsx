/**
 * Copyright (c) 2025 Andrew John Ward. All Rights Reserved.
 * PROPRIETARY AND CONFIDENTIAL - See LICENSE file for terms.
 */

'use client';

export const dynamic = 'force-dynamic';

import { MarketplaceLayout } from '@/components/layouts/MarketplaceLayout';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import Link from 'next/link';
import { useState } from 'react';

interface WebOSApp {
  id: string;
  name: string;
  description: string;
  category: string;
  icon: string;
  features: string[];
  popular: boolean;
}

const webOSApps: WebOSApp[] = [
  {
    id: 'terminal-pro',
    name: 'Terminal Pro',
    description:
      'Advanced terminal emulator with AI agent integration and intelligent command execution',
    category: 'Development',
    icon: '💻',
    features: [
      'AI autocomplete',
      'Agent integration',
      'Cloud sync',
      'Custom themes',
      'Collaboration',
    ],
    popular: true,
  },
  {
    id: 'code-editor-ai',
    name: 'Code Editor AI',
    description: 'Intelligent code editor with real-time AI suggestions and AI-driven refactoring',
    category: 'Development',
    icon: '📝',
    features: [
      'AI autocomplete',
      'Real-time suggestions',
      'Git integration',
      'Multi-language',
      'Code review',
    ],
    popular: true,
  },
  {
    id: 'database-browser',
    name: 'Database Browser',
    description: 'Visual database explorer with query builder and AI-powered optimization',
    category: 'Data',
    icon: '🗄️',
    features: [
      'SQL/NoSQL support',
      'Query builder',
      'AI optimization',
      'Visual schema',
      'Export tools',
    ],
    popular: false,
  },
  {
    id: 'api-client',
    name: 'API Client Elite',
    description: 'Modern API testing tool with environments, collections, and AI-generated tests',
    category: 'Development',
    icon: '🌐',
    features: [
      'Request builder',
      'Environments',
      'Collections',
      'AI test generation',
      'Team sharing',
    ],
    popular: true,
  },
  {
    id: 'deployment-manager',
    name: 'Deployment Manager',
    description: 'CI/CD pipeline manager with one-click deployments and rollback',
    category: 'DevOps',
    icon: '🚀',
    features: [
      'One-click deploy',
      'Rollback',
      'Pipeline visualization',
      'Multi-cloud',
      'Monitoring',
    ],
    popular: false,
  },
  {
    id: 'file-explorer-cloud',
    name: 'File Explorer Cloud',
    description: 'Cloud-native file manager with sync, share, and AI-powered organization',
    category: 'Productivity',
    icon: '📁',
    features: ['Cloud sync', 'Share links', 'AI organization', 'Search', 'Versioning'],
    popular: true,
  },
  {
    id: 'monitoring-dashboard',
    name: 'Monitoring Dashboard',
    description: 'Real-time system monitoring with performance metrics and intelligent alerts',
    category: 'DevOps',
    icon: '📊',
    features: [
      'Real-time metrics',
      'Custom dashboards',
      'Smart alerts',
      'UCF integration',
      'Team views',
    ],
    popular: false,
  },
  {
    id: 'collaboration-hub',
    name: 'Collaboration Hub',
    description: 'Team collaboration with shared workspaces, chat, and real-time sync',
    category: 'Productivity',
    icon: '👥',
    features: ['Shared workspaces', 'Team chat', 'Real-time collab', 'UCF sync', 'Video calls'],
    popular: true,
  },
  {
    id: 'design-studio',
    name: 'Design Studio',
    description: 'Visual design tool with AI assistance and intelligent layouts',
    category: 'Productivity',
    icon: '🎨',
    features: [
      'AI design suggestions',
      'Vector graphics',
      'Layer management',
      'Export to multiple formats',
      'Real-time collaboration',
    ],
    popular: true,
  },
  {
    id: 'email-client',
    name: 'Email Client',
    description: 'AI-powered email with smart filters and intelligent organization',
    category: 'Productivity',
    icon: '📧',
    features: [
      'AI email summaries',
      'Smart categorization',
      'Quick replies',
      'Search with AI',
      'Email scheduling',
    ],
    popular: true,
  },
  {
    id: 'video-editor',
    name: 'Video Editor',
    description: 'AI video editing in the browser with intelligent scene detection',
    category: 'Productivity',
    icon: '🎥',
    features: [
      'AI scene detection',
      'Timeline editing',
      'Transitions & effects',
      'Audio sync',
      'Export in 4K',
    ],
    popular: true,
  },
];

export default function WebOSMarketplacePage() {
  const [selectedApp, setSelectedApp] = useState<WebOSApp | null>(null);
  const [filter, setFilter] = useState<'all' | 'Development' | 'DevOps' | 'Productivity' | 'Data'>(
    'all'
  );

  const filteredApps =
    filter === 'all' ? webOSApps : webOSApps.filter((app) => app.category === filter);

  return (
    <MarketplaceLayout>
      <div className="bg-gradient-to-b from-background via-cyan-950 to-background">
        <div className="container mx-auto px-4 py-16">
          {/* Header */}
          <div className="mb-12">
            <Link
              href="/marketplace"
              className="text-ucf-harmony hover:text-ucf-harmony/80 mb-4 inline-block"
            >
              ← Back to Marketplace
            </Link>
            <h1 className="font-heading text-6xl font-bold mb-4 text-foreground">💻 Web OS Marketplace</h1>
            <p className="text-xl text-muted-foreground max-w-3xl">
              Pre-built Web OS applications for developers. Terminal, code editor, database browser,
              API client, and more. All with AI agent integration.
            </p>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-12">
            <div className="bg-cyan-900/30 rounded-lg p-6 border border-cyan-500/30">
              <div className="text-3xl font-bold text-cyan-400">{webOSApps.length}+</div>
              <div className="text-sm text-muted-foreground">Available Apps</div>
            </div>
            <div className="bg-blue-900/30 rounded-lg p-6 border border-blue-500/30">
              <div className="text-3xl font-bold text-blue-400">Included</div>
              <div className="text-sm text-muted-foreground">In Starter+ Plans</div>
            </div>
            <div className="bg-purple-900/30 rounded-lg p-6 border border-ucf-harmony/30">
              <div className="text-3xl font-bold text-ucf-harmony">AI-Powered</div>
              <div className="text-sm text-muted-foreground">All Apps</div>
            </div>
            <div className="bg-green-900/30 rounded-lg p-6 border border-green-500/30">
              <div className="text-3xl font-bold text-green-400">Cloud Sync</div>
              <div className="text-sm text-muted-foreground">Built-in</div>
            </div>
          </div>

          {/* Pricing Bundles */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            <Card className="bg-card/50 border-border p-6">
              <h3 className="text-xl font-bold text-foreground mb-2">Starter</h3>
              <div className="mb-4">
                <span className="text-4xl font-bold text-muted-foreground">$29</span>
                <span className="text-lg text-muted-foreground">/month</span>
              </div>
              <p className="text-muted-foreground text-sm mb-4">
                3 Web OS apps included with Starter plan
              </p>
              <Link href="/marketplace/pricing">
                <Button variant="outline" className="w-full border-border text-muted-foreground">
                  Get Starter
                </Button>
              </Link>
            </Card>

            <Card className="bg-gradient-to-br from-cyan-900/50 to-blue-900/50 border-cyan-500/50 p-6 shadow-lg shadow-cyan-500/20">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-xl font-bold text-foreground">Pro</h3>
                <span className="bg-cyan-500/20 text-cyan-400 px-2 py-1 rounded text-xs font-semibold">
                  BEST VALUE
                </span>
              </div>
              <div className="mb-4">
                <span className="text-4xl font-bold text-cyan-400">$79</span>
                <span className="text-lg text-muted-foreground">/month</span>
              </div>
              <p className="text-muted-foreground text-sm mb-4">
                All 12 Web OS apps + 24 agents, Discord bots, and more
              </p>
              <Link href="/marketplace/pricing">
                <Button className="w-full bg-cyan-600 hover:bg-cyan-700 text-white">Get Pro</Button>
              </Link>
            </Card>

            <Card className="bg-gradient-to-br from-purple-900/50 to-pink-900/50 border-ucf-harmony/50 p-6">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-xl font-bold text-foreground">Enterprise</h3>
                <span className="bg-purple-500/20 text-ucf-harmony px-2 py-1 rounded text-xs font-semibold">
                  UNLIMITED
                </span>
              </div>
              <div className="mb-4">
                <span className="text-4xl font-bold text-ucf-harmony">$299</span>
                <span className="text-lg text-muted-foreground">/month</span>
              </div>
              <p className="text-muted-foreground text-sm mb-4">
                All {webOSApps.length} apps + white-label, SSO, priority support
              </p>
              <Link href="/marketplace/pricing">
                <Button className="w-full bg-ucf-harmony hover:bg-ucf-harmony/90 text-white">
                  Get Enterprise
                </Button>
              </Link>
            </Card>
          </div>

          {/* Category Filter */}
          <div className="flex gap-4 mb-8 overflow-x-auto pb-4">
            {(['all', 'Development', 'DevOps', 'Productivity', 'Data'] as const).map((cat) => (
              <button
                key={cat}
                onClick={() => setFilter(cat)}
                className={`px-6 py-2 rounded-lg font-semibold whitespace-nowrap transition-all ${
                  filter === cat
                    ? 'bg-cyan-600 text-white'
                    : 'bg-muted/50 text-muted-foreground hover:bg-muted'
                }`}
              >
                {cat === 'all' ? 'All Apps' : cat}
              </button>
            ))}
          </div>

          {/* App Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
            {filteredApps.map((app) => (
              <AppCard key={app.id} app={app} onSelect={() => setSelectedApp(app)} />
            ))}
          </div>

          {/* Features Section */}
          <div className="bg-gradient-to-r from-cyan-900/40 to-blue-900/40 rounded-2xl p-8 border border-cyan-500/30 mb-16">
            <h2 className="font-heading text-3xl font-bold text-foreground mb-6">Why Web OS Apps?</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <div className="text-4xl mb-3">🤖</div>
                <h3 className="text-xl font-bold text-foreground mb-2">AI Agent Integration</h3>
                <p className="text-muted-foreground text-sm">
                  All apps integrate with Helix's 24 AI agents for intelligent assistance
                </p>
              </div>
              <div>
                <div className="text-4xl mb-3">☁️</div>
                <h3 className="text-xl font-bold text-foreground mb-2">Cloud Sync</h3>
                <p className="text-muted-foreground text-sm">
                  Your settings, data, and workflows sync across all devices
                </p>
              </div>
              <div>
                <div className="text-4xl mb-3">🧠</div>
                <h3 className="text-xl font-bold text-foreground mb-2">AI-Powered</h3>
                <p className="text-muted-foreground text-sm">
                  Apps adapt based on your UCF metrics for optimal productivity
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </MarketplaceLayout>
  );
}

function AppCard({ app, onSelect }: { app: WebOSApp; onSelect: () => void }) {
  const hasPage = ['design-studio', 'email-client', 'video-editor', 'code-editor-ai'].includes(
    app.id
  );
  const href =
    app.id === 'code-editor-ai'
      ? '/marketplace/web-os/code-editor'
      : hasPage
        ? `/marketplace/web-os/${app.id}`
        : '#';

  const CardContent = (
    <>
      <div className="flex items-start justify-between mb-4">
        <div className="text-5xl">{app.icon}</div>
        {app.popular && (
          <span className="bg-cyan-500/20 text-cyan-400 px-2 py-1 rounded text-xs font-semibold">
            🔥 Popular
          </span>
        )}
      </div>

      <h3 className="text-xl font-bold text-foreground mb-2">{app.name}</h3>
      <p className="text-muted-foreground text-sm mb-4 line-clamp-2">{app.description}</p>

      <div className="mb-4">
        <span className="bg-cyan-900/30 text-cyan-300 px-2 py-1 rounded text-xs">
          {app.category}
        </span>
      </div>

      <div className="mb-4">
        <div className="text-xs text-muted-foreground mb-2">Features:</div>
        <div className="flex flex-wrap gap-1">
          {app.features.slice(0, 3).map((feature, idx) => (
            <span key={idx} className="text-xs text-muted-foreground">
              • {feature}
            </span>
          ))}
        </div>
      </div>

      <div className="flex items-baseline justify-between">
        <div>
          <span className="text-sm font-semibold text-cyan-400">Included in Starter+</span>
        </div>
        <Button className="bg-cyan-600 hover:bg-cyan-700 text-white text-sm">
          {hasPage ? 'Try Demo →' : 'Learn More →'}
        </Button>
      </div>
    </>
  );

  if (hasPage) {
    return (
      <Link href={href}>
        <Card className="bg-card/50 border-border hover:border-cyan-500/50 transition-all cursor-pointer">
          <div className="p-6">{CardContent}</div>
        </Card>
      </Link>
    );
  }

  return (
    <Card className="bg-card/50 border-border hover:border-cyan-500/50 transition-all cursor-pointer">
      <div
        className="p-6"
        role="button"
        tabIndex={0}
        onClick={onSelect}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            onSelect();
          }
        }}
      >
        {CardContent}
      </div>
    </Card>
  );
}
