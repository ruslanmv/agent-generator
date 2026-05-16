// Docker wizard state — held at the page level. Kept small; the heavy
// state (project files, secrets) lives on the backend and is fetched
// on demand.

import { createContext, useContext } from 'react';

export type DockerStep = 0 | 1 | 2 | 3 | 4; // Configure / Env / Build / Publish / Published

export interface DockerConfig {
  image: string;            // registry/owner/name:tag
  baseImage: string;        // e.g. python:3.11-slim
  platforms: ('linux/amd64' | 'linux/arm64')[];
  pushOnBuild: boolean;
  signWithCosign: boolean;
  emitSBOM: boolean;
}

export const INITIAL_DOCKER: DockerConfig = {
  image: 'ghcr.io/example/agent:dev',
  baseImage: 'python:3.11-slim',
  platforms: ['linux/amd64'],
  pushOnBuild: false,
  signWithCosign: true,
  emitSBOM: true,
};

export interface DockerCtx {
  projectId: string;
  step: DockerStep;
  setStep: (s: DockerStep) => void;
  config: DockerConfig;
  setConfig: (next: DockerConfig) => void;
  buildId: string | null;
  setBuildId: (id: string | null) => void;
}

export const DockerContext = createContext<DockerCtx | null>(null);

export function useDocker(): DockerCtx {
  const ctx = useContext(DockerContext);
  if (!ctx) throw new Error('useDocker must be used inside <DockerContext>');
  return ctx;
}

export const DOCKER_STEPS = [
  'Configure',
  'Env / Secrets',
  'Build',
  'Publish',
  'Published',
];
