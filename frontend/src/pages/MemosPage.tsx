import { useState, useCallback, useRef } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CardMedia,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Grid2 as Grid,
  IconButton,
  InputAdornment,
  List,
  ListItem,
  ListItemSecondaryAction,
  ListItemText,
  Skeleton,
  Tab,
  Tabs,
  TextField,
  Typography,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import AddIcon from '@mui/icons-material/Add';
import TextSnippetIcon from '@mui/icons-material/TextSnippet';
import ImageIcon from '@mui/icons-material/Image';
import LinkIcon from '@mui/icons-material/Link';
import SettingsIcon from '@mui/icons-material/Settings';
import DragHandleIcon from '@mui/icons-material/DragHandle';
import {
  useMemos,
  useMemoCategories,
  useCreateMemoCategory,
  useUpdateMemoCategory,
  useDeleteMemoCategory,
  useUpdateMemoTags,
  useDeleteMemo,
} from '@/hooks/useMemos';
import type { Memo, MemoCategory, ContentType } from '@/types';

const CONTENT_TYPE_ICON: Record<ContentType, React.ReactElement> = {
  text: <TextSnippetIcon color="action" />,
  image: <ImageIcon color="primary" />,
  url: <LinkIcon color="secondary" />,
};

function MemoCard({
  memo,
  onDelete,
  onTagsUpdate,
}: {
  memo: Memo;
  onDelete: (id: string) => void;
  onTagsUpdate: (id: string, tags: string[]) => void;
}) {
  const [tagInput, setTagInput] = useState('');
  const [isEditingTags, setIsEditingTags] = useState(false);

  const handleAddTag = () => {
    const tag = tagInput.trim();
    if (tag && !memo.tags.includes(tag)) {
      onTagsUpdate(memo.id, [...memo.tags, tag]);
    }
    setTagInput('');
  };

  const handleRemoveTag = (tagToRemove: string) => {
    onTagsUpdate(memo.id, memo.tags.filter((t) => t !== tagToRemove));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag();
    }
  };

  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        transition: 'box-shadow 0.2s',
        '&:hover': { boxShadow: 4 },
      }}
    >
      {memo.contentType === 'image' && memo.imageUrl && (
        <CardMedia component="img" height="140" image={memo.imageUrl} alt="メモ画像" />
      )}
      {memo.contentType === 'url' && memo.urlThumbnail && (
        <CardMedia component="img" height="120" image={memo.urlThumbnail} alt={memo.urlTitle} />
      )}

      <CardContent sx={{ flex: 1, pb: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1 }}>
            {CONTENT_TYPE_ICON[memo.contentType]}
            <Typography variant="caption" color="text.secondary">
              {new Date(memo.createdAt).toLocaleDateString('ja-JP')}
            </Typography>
          </Box>
          <Box>
            <IconButton size="small" onClick={() => setIsEditingTags(!isEditingTags)}>
              <EditIcon fontSize="small" />
            </IconButton>
            <IconButton size="small" onClick={() => onDelete(memo.id)} color="error">
              <DeleteIcon fontSize="small" />
            </IconButton>
          </Box>
        </Box>

        {memo.contentType === 'url' ? (
          <>
            <Typography variant="body2" fontWeight="bold" gutterBottom noWrap>
              {memo.urlTitle || memo.content}
            </Typography>
            {memo.urlSummary && (
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                {memo.urlSummary}
              </Typography>
            )}
          </>
        ) : memo.contentType === 'image' ? (
          <>
            {memo.imageOcrText && (
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                OCR: {memo.imageOcrText.substring(0, 80)}
                {memo.imageOcrText.length > 80 ? '...' : ''}
              </Typography>
            )}
            <Typography variant="body2" noWrap>
              {memo.content}
            </Typography>
          </>
        ) : (
          <Typography
            variant="body2"
            sx={{
              display: '-webkit-box',
              WebkitLineClamp: 4,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
            }}
          >
            {memo.content}
          </Typography>
        )}

        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mt: 1 }}>
          {memo.tags.map((tag) => (
            <Chip
              key={tag}
              label={tag}
              size="small"
              variant="outlined"
              onDelete={isEditingTags ? () => handleRemoveTag(tag) : undefined}
            />
          ))}
        </Box>

        {isEditingTags && (
          <TextField
            size="small"
            placeholder="タグを追加..."
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            onKeyDown={handleKeyDown}
            onBlur={handleAddTag}
            sx={{ mt: 1 }}
            fullWidth
          />
        )}
      </CardContent>
    </Card>
  );
}

function CategoryManagementDialog({
  open,
  onClose,
  categories,
}: {
  open: boolean;
  onClose: () => void;
  categories: MemoCategory[];
}) {
  const [newCategoryName, setNewCategoryName] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingName, setEditingName] = useState('');

  const createCategory = useCreateMemoCategory();
  const updateCategory = useUpdateMemoCategory();
  const deleteCategory = useDeleteMemoCategory();

  const handleCreate = () => {
    const name = newCategoryName.trim();
    if (!name) return;
    createCategory.mutate({ name });
    setNewCategoryName('');
  };

  const handleRename = (id: string) => {
    const name = editingName.trim();
    if (!name) return;
    updateCategory.mutate({ id, name });
    setEditingId(null);
  };

  const handleDelete = (id: string) => {
    deleteCategory.mutate(id);
  };

  const startEditing = (cat: MemoCategory) => {
    setEditingId(cat.id);
    setEditingName(cat.name);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>カテゴリ管理</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
          <TextField
            size="small"
            placeholder="新しいカテゴリ名"
            value={newCategoryName}
            onChange={(e) => setNewCategoryName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleCreate();
            }}
            fullWidth
          />
          <Button
            variant="contained"
            size="small"
            onClick={handleCreate}
            disabled={!newCategoryName.trim() || createCategory.isPending}
            startIcon={<AddIcon />}
          >
            追加
          </Button>
        </Box>

        <List dense>
          {categories.map((cat) => (
            <ListItem key={cat.id} sx={{ bgcolor: 'grey.50', borderRadius: 1, mb: 0.5 }}>
              <DragHandleIcon sx={{ color: 'text.disabled', mr: 1 }} />
              {editingId === cat.id ? (
                <TextField
                  size="small"
                  value={editingName}
                  onChange={(e) => setEditingName(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleRename(cat.id);
                    if (e.key === 'Escape') setEditingId(null);
                  }}
                  onBlur={() => handleRename(cat.id)}
                  autoFocus
                  fullWidth
                />
              ) : (
                <ListItemText
                  primary={cat.name}
                  secondary={cat.isDefault ? 'デフォルト' : undefined}
                />
              )}
              <ListItemSecondaryAction>
                {editingId !== cat.id && (
                  <IconButton size="small" onClick={() => startEditing(cat)}>
                    <EditIcon fontSize="small" />
                  </IconButton>
                )}
                {!cat.isDefault && (
                  <IconButton
                    size="small"
                    color="error"
                    onClick={() => handleDelete(cat.id)}
                    disabled={deleteCategory.isPending}
                  >
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                )}
              </ListItemSecondaryAction>
            </ListItem>
          ))}
        </List>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>閉じる</Button>
      </DialogActions>
    </Dialog>
  );
}

function MemosPage() {
  const [selectedCategory, setSelectedCategory] = useState<string | undefined>(undefined);
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [categoryDialogOpen, setCategoryDialogOpen] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  const debounceTimer = useRef<ReturnType<typeof setTimeout>>();

  const { data: categories = [] } = useMemoCategories();
  const {
    data: memosData,
    isLoading,
    isError,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useMemos({ categoryId: selectedCategory, search: debouncedSearch });
  const updateTags = useUpdateMemoTags();
  const deleteMemo = useDeleteMemo();

  const memos = memosData?.pages.flatMap((page) => page.items) ?? [];

  const handleSearchChange = useCallback((value: string) => {
    setSearchQuery(value);
    clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => {
      setDebouncedSearch(value);
    }, 400);
  }, []);

  const handleTagsUpdate = (id: string, tags: string[]) => {
    updateTags.mutate({ id, tags });
  };

  const handleDeleteConfirm = () => {
    if (deleteConfirm) {
      deleteMemo.mutate(deleteConfirm);
      setDeleteConfirm(null);
    }
  };

  // Infinite scroll observer
  const observerRef = useRef<IntersectionObserver>();
  const lastCardRef = useCallback(
    (node: HTMLElement | null) => {
      if (isFetchingNextPage) return;
      if (observerRef.current) observerRef.current.disconnect();
      observerRef.current = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting && hasNextPage) {
          fetchNextPage();
        }
      });
      if (node) observerRef.current.observe(node);
    },
    [isFetchingNextPage, hasNextPage, fetchNextPage],
  );

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5" fontWeight="bold">
          メモ管理
        </Typography>
        <Button
          variant="outlined"
          size="small"
          startIcon={<SettingsIcon />}
          onClick={() => setCategoryDialogOpen(true)}
        >
          カテゴリ管理
        </Button>
      </Box>

      {/* Search */}
      <TextField
        placeholder="メモを検索..."
        value={searchQuery}
        onChange={(e) => handleSearchChange(e.target.value)}
        fullWidth
        size="small"
        sx={{ mb: 2 }}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchIcon />
            </InputAdornment>
          ),
        }}
      />

      {/* Category Tabs */}
      <Tabs
        value={selectedCategory ?? 'all'}
        onChange={(_, val) => setSelectedCategory(val === 'all' ? undefined : val)}
        variant="scrollable"
        scrollButtons="auto"
        sx={{ mb: 3, borderBottom: 1, borderColor: 'divider' }}
      >
        <Tab label="すべて" value="all" />
        {categories.map((cat: MemoCategory) => (
          <Tab key={cat.id} label={cat.name} value={cat.id} />
        ))}
      </Tabs>

      {/* Error */}
      {isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          メモの読み込みに失敗しました
        </Alert>
      )}

      {/* Loading skeleton */}
      {isLoading && (
        <Grid container spacing={2}>
          {[...Array(6)].map((_, i) => (
            <Grid key={i} size={{ xs: 12, sm: 6, md: 4 }}>
              <Skeleton variant="rectangular" height={200} sx={{ borderRadius: 1 }} />
            </Grid>
          ))}
        </Grid>
      )}

      {/* Empty */}
      {!isLoading && !isError && memos.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography variant="body1" color="text.secondary">
            {debouncedSearch ? '検索結果が見つかりません' : 'メモはまだありません'}
          </Typography>
        </Box>
      )}

      {/* Memo Grid */}
      {!isLoading && !isError && memos.length > 0 && (
        <Grid container spacing={2}>
          {memos.map((memo: Memo, index: number) => (
            <Grid
              key={memo.id}
              size={{ xs: 12, sm: 6, md: 4 }}
              ref={index === memos.length - 1 ? lastCardRef : undefined}
            >
              <MemoCard
                memo={memo}
                onDelete={(id) => setDeleteConfirm(id)}
                onTagsUpdate={handleTagsUpdate}
              />
            </Grid>
          ))}
        </Grid>
      )}

      {/* Loading more */}
      {isFetchingNextPage && (
        <Box sx={{ textAlign: 'center', py: 3 }}>
          <CircularProgress size={28} />
        </Box>
      )}

      {/* Delete confirmation dialog */}
      <Dialog open={!!deleteConfirm} onClose={() => setDeleteConfirm(null)}>
        <DialogTitle>メモを削除</DialogTitle>
        <DialogContent>
          <DialogContentText>
            このメモを削除しますか？この操作は取り消せます。
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteConfirm(null)}>キャンセル</Button>
          <Button onClick={handleDeleteConfirm} color="error" variant="contained">
            削除
          </Button>
        </DialogActions>
      </Dialog>

      {/* Category management dialog */}
      <CategoryManagementDialog
        open={categoryDialogOpen}
        onClose={() => setCategoryDialogOpen(false)}
        categories={categories}
      />
    </Box>
  );
}

export default MemosPage;
