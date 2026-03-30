'use client';

import { MarketplaceLayout } from '@/components/layouts/MarketplaceLayout';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { designStudioAPI, type DesignProject } from '@/lib/web-os-api';
import { logger } from '@/lib/logger';
import {
  Circle,
  Download,
  FolderOpen,
  Layers,
  Move,
  Palette,
  Redo,
  Save,
  Sparkles,
  Square,
  Trash2,
  Type,
  Undo,
  ZoomIn,
  ZoomOut,
} from 'lucide-react';
import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';

type Tool = 'select' | 'rectangle' | 'circle' | 'text' | 'image';
type Shape = {
  id: string;
  type: 'rectangle' | 'circle' | 'text' | 'image';
  x: number;
  y: number;
  width: number;
  height: number;
  color: string;
  text?: string;
  imageUrl?: string;
};

export default function DesignStudioPage() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [tool, setTool] = useState<Tool>('select');
  const [color, setColor] = useState('#3b82f6');
  const [shapes, setShapes] = useState<Shape[]>([]);
  const [selectedShape, setSelectedShape] = useState<string | null>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [startPos, setStartPos] = useState({ x: 0, y: 0 });
  const [history, setHistory] = useState<Shape[][]>([[]]);
  const [historyIndex, setHistoryIndex] = useState(0);
  const [aiSuggestion, setAiSuggestion] = useState('');
  const [velocity, setVelocity] = useState(1);

  // API state
  const [currentProject, setCurrentProject] = useState<DesignProject | null>(null);
  const [projects, setProjects] = useState<DesignProject[]>([]);
  const [projectName, setProjectName] = useState('Untitled Design');
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [showProjects, setShowProjects] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    drawCanvas();
  }, [shapes, selectedShape, velocity]);

  const drawCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#1e293b';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.save();
    ctx.scale(velocity, velocity);

    shapes.forEach((shape) => {
      ctx.fillStyle = shape.color;
      ctx.strokeStyle = selectedShape === shape.id ? '#fbbf24' : shape.color;
      ctx.lineWidth = selectedShape === shape.id ? 3 / velocity : 1 / velocity;

      switch (shape.type) {
        case 'rectangle':
          ctx.fillRect(shape.x, shape.y, shape.width, shape.height);
          ctx.strokeRect(shape.x, shape.y, shape.width, shape.height);
          break;
        case 'circle':
          ctx.beginPath();
          ctx.arc(
            shape.x + shape.width / 2,
            shape.y + shape.height / 2,
            Math.min(shape.width, shape.height) / 2,
            0,
            Math.PI * 2
          );
          ctx.fill();
          ctx.stroke();
          break;
        case 'text':
          ctx.font = `${24 / velocity}px Arial`;
          ctx.fillText(shape.text || 'Text', shape.x, shape.y + 24);
          break;
      }
    });

    ctx.restore();
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left) / velocity;
    const y = (e.clientY - rect.top) / velocity;

    if (tool === 'select') {
      const clicked = shapes.find(
        (shape) =>
          x >= shape.x && x <= shape.x + shape.width && y >= shape.y && y <= shape.y + shape.height
      );
      setSelectedShape(clicked?.id || null);
    } else {
      setIsDrawing(true);
      setStartPos({ x, y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left) / velocity;
    const y = (e.clientY - rect.top) / velocity;

    const tempShape: Shape = {
      id: 'temp',
      type: tool === 'rectangle' ? 'rectangle' : 'circle',
      x: Math.min(startPos.x, x),
      y: Math.min(startPos.y, y),
      width: Math.abs(x - startPos.x),
      height: Math.abs(y - startPos.y),
      color: color,
    };

    setShapes([...shapes.filter((s) => s.id !== 'temp'), tempShape]);
  };

  const handleMouseUp = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return;
    setIsDrawing(false);

    const tempShape = shapes.find((s) => s.id === 'temp');
    if (tempShape && tempShape.width > 5 && tempShape.height > 5) {
      const newShape = { ...tempShape, id: Date.now().toString() };
      const newShapes = [...shapes.filter((s) => s.id !== 'temp'), newShape];
      setShapes(newShapes);
      addToHistory(newShapes);
    } else {
      setShapes(shapes.filter((s) => s.id !== 'temp'));
    }
  };

  const addToHistory = (newShapes: Shape[]) => {
    const newHistory = history.slice(0, historyIndex + 1);
    newHistory.push(newShapes);
    setHistory(newHistory);
    setHistoryIndex(newHistory.length - 1);
  };

  const undo = () => {
    if (historyIndex > 0) {
      setHistoryIndex(historyIndex - 1);
      setShapes(history[historyIndex - 1]);
    }
  };

  const redo = () => {
    if (historyIndex < history.length - 1) {
      setHistoryIndex(historyIndex + 1);
      setShapes(history[historyIndex + 1]);
    }
  };

  const deleteSelected = () => {
    if (selectedShape) {
      const newShapes = shapes.filter((s) => s.id !== selectedShape);
      setShapes(newShapes);
      addToHistory(newShapes);
      setSelectedShape(null);
    }
  };

  const generateAISuggestion = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const result = await designStudioAPI.getAISuggestions({
        shapes,
        velocity,
      });
      setAiSuggestion(
        result.suggestions[0] +
          '\nColor palette: ' +
          result.color_palette.join(', ') +
          '\n' +
          result.layout_tips[0]
      );
    } catch (err) {
      logger.warn('Design AI unavailable:', err);
      setAiSuggestion('AI design assistant is currently unavailable. Please try again later.');
    } finally {
      setIsLoading(false);
    }
  };

  const saveProject = async () => {
    try {
      setIsSaving(true);
      setError(null);
      const canvasData = {
        shapes,
        velocity,
      };

      if (currentProject) {
        // Update existing project
        const updated = await designStudioAPI.updateProject(currentProject.id, {
          name: projectName,
          canvas_data: canvasData,
        });
        setCurrentProject(updated);
      } else {
        // Create new project
        const created = await designStudioAPI.createProject({
          name: projectName,
          canvas_data: canvasData,
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
      const loadedProjects = await designStudioAPI.listProjects();
      setProjects(loadedProjects);
      setShowProjects(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load projects');
    } finally {
      setIsLoading(false);
    }
  };

  const loadProject = (project: DesignProject) => {
    setCurrentProject(project);
    setProjectName(project.name);
    setShapes(project.canvas_data.shapes);
    setVelocity(project.canvas_data.velocity);
    setHistory([project.canvas_data.shapes]);
    setHistoryIndex(0);
    setShowProjects(false);
  };

  const newProject = () => {
    setCurrentProject(null);
    setProjectName('Untitled Design');
    setShapes([]);
    setVelocity(1);
    setHistory([[]]);
    setHistoryIndex(0);
    setShowProjects(false);
  };

  const exportDesign = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const link = document.createElement('a');
    link.download = 'helix-design.png';
    link.href = canvas.toDataURL();
    link.click();
  };

  const addText = () => {
    const newShape: Shape = {
      id: Date.now().toString(),
      type: 'text',
      x: 100,
      y: 100,
      width: 200,
      height: 30,
      color: color,
      text: 'Edit me!',
    };
    const newShapes = [...shapes, newShape];
    setShapes(newShapes);
    addToHistory(newShapes);
  };

  return (
    <MarketplaceLayout>
      <div className="min-h-screen bg-gradient-to-b from-background via-purple-950 to-background">
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
                  🎨 Design Studio
                </h1>
                <p className="text-muted-foreground">Visual design tool with AI assistance</p>
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
                          {project.canvas_data.shapes.length} shapes • Last updated:{' '}
                          {new Date(project.updated_at).toLocaleDateString()}
                        </p>
                      </Card>
                    ))
                  )}
                </div>
              </Card>
            </div>
          )}

          {/* Main Editor */}
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
            {/* Toolbar */}
            <Card className="lg:col-span-1 bg-card/50 backdrop-blur-sm border-border p-4">
              <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
                <Palette className="h-5 w-5" />
                Tools
              </h3>

              {/* Tool Selection */}
              <div className="space-y-2 mb-6">
                <Button
                  variant={tool === 'select' ? 'default' : 'outline'}
                  className="w-full justify-start"
                  onClick={() => setTool('select')}
                >
                  <Move className="h-4 w-4 mr-2" />
                  Select
                </Button>
                <Button
                  variant={tool === 'rectangle' ? 'default' : 'outline'}
                  className="w-full justify-start"
                  onClick={() => setTool('rectangle')}
                >
                  <Square className="h-4 w-4 mr-2" />
                  Rectangle
                </Button>
                <Button
                  variant={tool === 'circle' ? 'default' : 'outline'}
                  className="w-full justify-start"
                  onClick={() => setTool('circle')}
                >
                  <Circle className="h-4 w-4 mr-2" />
                  Circle
                </Button>
                <Button variant="outline" className="w-full justify-start" onClick={addText}>
                  <Type className="h-4 w-4 mr-2" />
                  Add Text
                </Button>
              </div>

              {/* Color Picker */}
              <div className="mb-6">
                <label className="text-sm text-muted-foreground mb-2 block">Color</label>
                <input
                  type="color"
                  value={color}
                  onChange={(e) => setColor(e.target.value)}
                  className="w-full h-10 rounded cursor-pointer"
                />
              </div>

              {/* Actions */}
              <div className="space-y-2 mb-6">
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={undo}
                  disabled={historyIndex === 0}
                >
                  <Undo className="h-4 w-4 mr-2" />
                  Undo
                </Button>
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={redo}
                  disabled={historyIndex === history.length - 1}
                >
                  <Redo className="h-4 w-4 mr-2" />
                  Redo
                </Button>
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={deleteSelected}
                  disabled={!selectedShape}
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete
                </Button>
              </div>

              {/* Velocity */}
              <div className="space-y-2 mb-6">
                <label className="text-sm text-muted-foreground block">
                  Velocity: {Math.round(velocity * 100)}%
                </label>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setVelocity(Math.max(0.5, velocity - 0.1))}
                  >
                    <ZoomOut className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setVelocity(Math.min(2, velocity + 0.1))}
                  >
                    <ZoomIn className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              {/* AI Assistance */}
              <Button
                className="w-full bg-purple-600 hover:bg-purple-700"
                onClick={generateAISuggestion}
                disabled={isLoading}
              >
                <Sparkles className="h-4 w-4 mr-2" />
                {isLoading ? 'Generating...' : 'AI Suggestion'}
              </Button>

              {aiSuggestion && (
                <Card className="mt-4 p-3 bg-purple-500/10 border-purple-500/30">
                  <p className="text-sm text-purple-200">{aiSuggestion}</p>
                </Card>
              )}
            </Card>

            {/* Canvas */}
            <Card className="lg:col-span-3 bg-card/50 backdrop-blur-sm border-border p-4">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
                  <Layers className="h-5 w-5" />
                  Canvas ({shapes.length} objects)
                </h3>
                <Button className="bg-green-600 hover:bg-green-700" onClick={exportDesign}>
                  <Download className="h-4 w-4 mr-2" />
                  Export PNG
                </Button>
              </div>

              <canvas
                ref={canvasRef}
                width={800}
                height={600}
                className="w-full border border-border rounded-lg cursor-crosshair"
                onMouseDown={handleMouseDown}
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
              />

              <div className="mt-4 text-sm text-muted-foreground">
                <p>
                  <strong>Tip:</strong> Select a tool, choose a color, and click-drag on the canvas
                  to create shapes. Use AI Suggestion for design tips!
                </p>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </MarketplaceLayout>
  );
}
