% Run every stem script in this folder (MATLAB or Octave).
files = dir('stem_*.m');
for k = 1:numel(files)
  [~, nm] = fileparts(files(k).name);
  fprintf('%s\n', nm);
  run(files(k).name);
end
