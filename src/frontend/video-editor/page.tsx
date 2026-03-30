'use client';

import { MarketplaceLayout } from '@/components/layouts/MarketplaceLayout';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { useToast } from '@/components/ui/use-toast';
import { videoEditorAPI, type VideoProject } from '@/lib/web-os-api';
import {
  Download,
  FolderOpen,
  Image as ImageIcon,
  Layers,
  Music,
  Pause,
  Play,
  Save,
  Scissors,
  SkipBack,
  SkipForward,
  Sparkles,
  Trash2,
  Type,
  Video,
} from 'lucide-react';
import Link from 'next/link';
import { useRef, useState } from 'react';

type TimelineClip = {
  id: string;
  type: 'video' | 'audio' | 'text' | 'image';
  name: string;
  start: number;
  duration: number;
  color: string;
};

export default function VideoEditorPage() {
  const [clips, setClips] = useState<TimelineClip[]>([
    {
      id: '1',
      type: 'video',
      name: 'Intro Clip',
      start: 0,
      duration: 5,
      color: '#3b82f6',
    },
    {
      id: '2',
      type: 'video',
      name: 'Main Content',
      start: 5,
      duration: 10,
      color: '#3b82f6',
    },
  ]);
  const [selectedClip, setSelectedClip] = useState<string | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [totalDuration, setTotalDuration] = useState(15);
  const [velocity, setVelocity] = useState(1);
  const { toast } = useToast();
  const timelineRef = useRef<HTMLDivElement>(null);

  // API state
  const [currentProject, setCurrentProject] = useState<VideoProject | null>(null);
  const [projects, setProjects] = useState<VideoProject[]>([]);
  const [projectName, setProjectName] = useState('Untitled Video');
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [showProjects, setShowProjects] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const pixelsPerSecond = 50 * velocity;

  const addClip = (type: TimelineClip['type']) => {
    const lastClip = clips[clips.length - 1];
    const start = lastClip ? lastClip.start + lastClip.duration : 0;

    const colors = {
      video: '#3b82f6',
      audio: '#10b981',
      text: '#f59e0b',
      image: '#8b5cf6',
    };

    const newClip: TimelineClip = {
      id: Date.now().toString(),
      type,
      name: `${type.charAt(0).toUpperCase() + type.slice(1)} Clip`,
      start,
      duration: 3,
      color: colors[type],
    };

    setClips([...clips, newClip]);
    setTotalDuration(Math.max(totalDuration, start + 3));
  };

  const deleteClip = (clipId: string) => {
    setClips(clips.filter((c) => c.id !== clipId));
    if (selectedClip === clipId) {
      setSelectedClip(null);
    }
  };

  const splitClip = () => {
    if (!selectedClip) return;

    const clip = clips.find((c) => c.id === selectedClip);
    if (!clip || currentTime < clip.start || currentTime > clip.start + clip.duration) return;

    const splitPoint = currentTime - clip.start;
    const newClip1: TimelineClip = {
      ...clip,
      duration: splitPoint,
    };
    const newClip2: TimelineClip = {
      ...clip,
      id: Date.now().toString(),
      start: clip.start + splitPoint,
      duration: clip.duration - splitPoint,
    };

    setClips(clips.map((c) => (c.id === selectedClip ? newClip1 : c)).concat(newClip2));
  };

  const togglePlayback = () => {
    setIsPlaying(!isPlaying);
    // In a real implementation, this would control actual video playback
  };

  const aiDetectScenes = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const result = await videoEditorAPI.detectScenes('https://example.com/video.mp4');
      // Add detected scenes as markers or clips
      const newClips = result.scenes.map((scene, idx) => ({
        id: `scene-${Date.now()}-${idx}`,
        type: 'video' as const,
        name: scene.description,
        start: scene.start,
        duration: scene.end - scene.start,
        color: '#3b82f6',
      }));
      setClips([...clips, ...newClips]);
    } catch (err) {
      setError('Failed to detect scenes (using demo mode)');
    } finally {
      setIsLoading(false);
    }
  };

  const aiGenerateSubtitles = () => {
    const textClip: TimelineClip = {
      id: Date.now().toString(),
      type: 'text',
      name: 'Auto-generated Subtitles',
      start: 0,
      duration: totalDuration,
      color: '#f59e0b',
    };
    setClips([...clips, textClip]);
  };

  const saveProject = async () => {
    try {
      setIsSaving(true);
      setError(null);
      const timelineData = {
        clips: clips.map((c) => ({
          id: c.id,
          type: c.type,
          start: c.start,
          duration: c.duration,
        })),
        duration: totalDuration,
      };

      if (currentProject) {
        const updated = await videoEditorAPI.updateProject(currentProject.id, {
          name: projectName,
          timeline_data: timelineData,
        });
        setCurrentProject(updated);
      } else {
        const created = await videoEditorAPI.createProject({
          name: projectName,
          timeline_data: timelineData,
          resolution: '1920x1080',
          fps: 30,
        });
        setCurrentProject(created);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save project');
    } finally {
      setIsSaving(false);
    }
  };

  const loadProjects = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const loadedProjects = await videoEditorAPI.listProjects();
      setProjects(loadedProjects);
      setShowProjects(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load projects');
    } finally {
      setIsLoading(false);
    }
  };

  const loadProject = (project: VideoProject) => {
    setCurrentProject(project);
    setProjectName(project.name);
    const loadedClips = project.timeline_data.clips.map((c) => ({
      ...c,
      name: `${c.type.charAt(0).toUpperCase() + c.type.slice(1)} Clip`,
      color:
        c.type === 'video'
          ? '#3b82f6'
          : c.type === 'audio'
            ? '#10b981'
            : c.type === 'text'
              ? '#f59e0b'
              : '#8b5cf6',
    }));
    setClips(loadedClips);
    setTotalDuration(project.timeline_data.duration);
    setShowProjects(false);
  };

  const newProject = () => {
    setCurrentProject(null);
    setProjectName('Untitled Video');
    setClips([]);
    setTotalDuration(15);
    setShowProjects(false);
  };

  const exportVideo = async () => {
    if (!currentProject) {
      setError('Please save the project before exporting');
      return;
    }
    try {
      setIsLoading(true);
      setError(null);
      const result = await videoEditorAPI.exportProject(currentProject.id, 'mp4', 'high');
      setError(null);
      toast({
        title: 'Export Queued',
        description: `Export ID: ${result.export_id} — MP4 (H.264), 1920x1080, ${totalDuration}s, ${clips.length} clips`,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to export video');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <MarketplaceLayout>
      <div className="min-h-screen bg-gradient-to-b from-background via-indigo-950 to-background">
        <div className="container mx-auto px-4 py-8">
          {/* Header */}
          <div className="mb-6">
            <Link
              href="/marketplace/web-os"
              className="text-ucf-harmony hover:text-ucf-harmony/80 mb-4 inline-block"
            >
              ← Back to Web OS
            </Link>
            <div className="flex items-center justify-between">
              <div>
                <h1 className="font-heading text-4xl font-bold mb-2 text-foreground">
                  🎥 Video Editor
                </h1>
                <p className="text-muted-foreground">AI video editing in the browser</p>
              </div>
              <div className="flex gap-2">
                <Button onClick={newProject} variant="outline">
                  New Project
                </Button>
                <Button onClick={loadProjects} variant="outline" disabled={isLoading}>
                  <FolderOpen className="h-4 w-4 mr-2" />
                  {isLoading ? 'Loading...' : 'Open'}
                </Button>
                <Button onClick={saveProject} disabled={isSaving}>
                  <Save className="h-4 w-4 mr-2" />
                  {isSaving ? 'Saving...' : 'Save'}
                </Button>
              </div>
            </div>
            {currentProject && (
              <input
                type="text"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                className="mt-2 px-3 py-1 bg-background border border-border rounded text-sm"
                placeholder="Project name"
              />
            )}
            {error && (
              <Card className="mt-2 p-3 bg-red-500/10 border-red-500/30">
                <p className="text-sm text-red-200">{error}</p>
              </Card>
            )}
          </div>

          {/* Projects List Modal */}
          {showProjects && (
            <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
              <Card className="max-w-2xl w-full max-h-[80vh] overflow-auto p-6 bg-card border-border">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="font-heading text-2xl font-bold">Your Projects</h2>
                  <Button onClick={() => setShowProjects(false)} variant="ghost">
                    ✕
                  </Button>
                </div>
                <div className="grid grid-cols-1 gap-3">
                  {projects.length === 0 ? (
                    <p className="text-muted-foreground text-center py-8">No projects yet</p>
                  ) : (
                    projects.map((project) => (
                      <Card
                        key={project.id}
                        className="p-4 hover:bg-accent cursor-pointer transition-colors"
                        onClick={() => loadProject(project)}
                      >
                        <h3 className="font-semibold">{project.name}</h3>
                        <p className="text-sm text-muted-foreground">
                          {project.timeline_data.clips.length} clips • {project.resolution} @{' '}
                          {project.fps}fps • Last updated:{' '}
                          {new Date(project.updated_at).toLocaleDateString()}
                        </p>
                      </Card>
                    ))
                  )}
                </div>
              </Card>
            </div>
          )}

          {/* Video Editor Interface */}
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
            {/* Toolbar */}
            <Card className="lg:col-span-1 bg-card/50 backdrop-blur-sm border-border p-4">
              <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
                <Layers className="h-5 w-5" />
                Tools
              </h3>

              {/* Add Clips */}
              <div className="space-y-2 mb-6">
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => addClip('video')}
                >
                  <Video className="h-4 w-4 mr-2" />
                  Add Video
                </Button>
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => addClip('audio')}
                >
                  <Music className="h-4 w-4 mr-2" />
                  Add Audio
                </Button>
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => addClip('text')}
                >
                  <Type className="h-4 w-4 mr-2" />
                  Add Text
                </Button>
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => addClip('image')}
                >
                  <ImageIcon className="h-4 w-4 mr-2" />
                  Add Image
                </Button>
              </div>

              {/* Edit Actions */}
              <div className="space-y-2 mb-6">
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={splitClip}
                  disabled={!selectedClip}
                >
                  <Scissors className="h-4 w-4 mr-2" />
                  Split Clip
                </Button>
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => selectedClip && deleteClip(selectedClip)}
                  disabled={!selectedClip}
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete Clip
                </Button>
              </div>

              {/* AI Features */}
              <div className="mb-6">
                <h4 className="text-sm font-medium text-foreground mb-2">AI Features</h4>
                <div className="space-y-2">
                  <Button
                    variant="outline"
                    className="w-full justify-start"
                    onClick={aiDetectScenes}
                    disabled={isLoading}
                  >
                    <Sparkles className="h-4 w-4 mr-2" />
                    {isLoading ? 'Detecting...' : 'Detect Scenes'}
                  </Button>
                  <Button
                    variant="outline"
                    className="w-full justify-start"
                    onClick={aiGenerateSubtitles}
                  >
                    <Type className="h-4 w-4 mr-2" />
                    Generate Subtitles
                  </Button>
                </div>
              </div>

              {/* Export */}
              <Button
                className="w-full bg-green-600 hover:bg-green-700"
                onClick={exportVideo}
                disabled={isLoading || !currentProject}
              >
                <Download className="h-4 w-4 mr-2" />
                {isLoading ? 'Exporting...' : 'Export Video'}
              </Button>
            </Card>

            {/* Main Editor */}
            <Card className="lg:col-span-3 bg-card/50 backdrop-blur-sm border-border p-4">
              {/* Preview Area */}
              <div className="mb-6">
                <div className="aspect-video bg-card rounded-lg flex items-center justify-center border border-border">
                  <div className="text-center">
                    <Video className="h-16 w-16 mx-auto mb-4 text-muted-foreground" />
                    <p className="text-muted-foreground mb-2">Video Preview</p>
                    <p className="text-sm text-muted-foreground">
                      {Math.floor(currentTime / 60)}:
                      {(currentTime % 60).toString().padStart(2, '0')} /{' '}
                      {Math.floor(totalDuration / 60)}:
                      {(totalDuration % 60).toString().padStart(2, '0')}
                    </p>
                  </div>
                </div>
              </div>

              {/* Playback Controls */}
              <div className="flex items-center justify-center gap-4 mb-6">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentTime(Math.max(0, currentTime - 1))}
                >
                  <SkipBack className="h-4 w-4" />
                </Button>
                <Button className="bg-indigo-600 hover:bg-indigo-700" onClick={togglePlayback}>
                  {isPlaying ? <Pause className="h-5 w-5" /> : <Play className="h-5 w-5" />}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentTime(Math.min(totalDuration, currentTime + 1))}
                >
                  <SkipForward className="h-4 w-4" />
                </Button>
              </div>

              {/* Timeline */}
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-lg font-semibold text-foreground">
                    Timeline ({clips.length} clips)
                  </h3>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setVelocity(Math.max(0.5, velocity - 0.25))}
                    >
                      -
                    </Button>
                    <span className="text-sm text-muted-foreground px-2">
                      {Math.round(velocity * 100)}%
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setVelocity(Math.min(2, velocity + 0.25))}
                    >
                      +
                    </Button>
                  </div>
                </div>

                <div
                  ref={timelineRef}
                  className="relative bg-card rounded-lg p-4 overflow-x-auto border border-border"
                  style={{ minHeight: '200px' }}
                >
                  {/* Time markers */}
                  <div className="flex mb-2 text-xs text-muted-foreground">
                    {Array.from({ length: Math.ceil(totalDuration) + 1 }, (_, i) => (
                      <div
                        key={i}
                        style={{ width: `${pixelsPerSecond}px` }}
                        className="border-l border-border pl-1"
                      >
                        {i}s
                      </div>
                    ))}
                  </div>

                  {/* Clips */}
                  <div
                    className="relative"
                    style={{
                      minWidth: `${totalDuration * pixelsPerSecond}px`,
                      height: '120px',
                    }}
                  >
                    {clips.map((clip, index) => (
                      <div
                        key={clip.id}
                        className={`absolute h-10 rounded cursor-pointer transition-all ${
                          selectedClip === clip.id ? 'ring-2 ring-yellow-400' : ''
                        }`}
                        style={{
                          left: `${clip.start * pixelsPerSecond}px`,
                          width: `${clip.duration * pixelsPerSecond}px`,
                          backgroundColor: clip.color,
                          top: `${(index % 3) * 40}px`,
                        }}
                        onClick={() => setSelectedClip(clip.id)}
                      >
                        <div className="px-2 py-1 text-xs text-white truncate">{clip.name}</div>
                      </div>
                    ))}

                    {/* Playhead */}
                    <div
                      className="absolute top-0 bottom-0 w-0.5 bg-red-500 z-10"
                      style={{ left: `${currentTime * pixelsPerSecond}px` }}
                    >
                      <div className="absolute -top-2 left-1/2 transform -translate-x-1/2 w-3 h-3 bg-red-500 rounded-full" />
                    </div>
                  </div>
                </div>
              </div>

              {/* Selected Clip Info */}
              {selectedClip && (
                <Card className="bg-indigo-500/10 border-indigo-500/30 p-3">
                  {(() => {
                    const clip = clips.find((c) => c.id === selectedClip);
                    return clip ? (
                      <div className="text-sm">
                        <div className="font-medium text-foreground mb-1">{clip.name}</div>
                        <div className="text-muted-foreground">
                          Type: {clip.type} | Start: {clip.start.toFixed(1)}s | Duration:{' '}
                          {clip.duration.toFixed(1)}s
                        </div>
                      </div>
                    ) : null;
                  })()}
                </Card>
              )}
            </Card>
          </div>
        </div>
      </div>
    </MarketplaceLayout>
  );
}
