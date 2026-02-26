import React, { useState } from "react";
import {
  Box,
  Collapse,
  IconButton,
  Skeleton,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { Flag, KeyboardArrowDown, KeyboardArrowRight, Layers, Token } from "@mui/icons-material";
import { useNavigate } from "react-router-dom";
import type { Episode } from "../../types/trace";
import TraceRows from "./TraceRows";
import {
  episodeGetAverageConfidence,
  episodeGetDuration,
  episodeGetPriority,
  episodeGetStartTime,
  episodeGetStatus,
  episodeGetTotalTokens,
} from "../utils/episodeUtils";
import { formatDateTime, getPriorityColor } from "../utils/utils";
import TypeChip from "./TypeChip";
import StatusChip from "./StatusChip";
import ConfidenceIndicator from "./ConfidenceIndicator";

const EpisodeRow: React.FC<{ episode: Episode }> = ({ episode }) => {
  const [open, setOpen] = useState(false);
  const nav = useNavigate();
  const startTime = episodeGetStartTime(episode);
  const totalTokens = episodeGetTotalTokens(episode) ?? "N/A";
  const priority = episodeGetPriority(episode);
  const duration = episodeGetDuration(episode);
  const status = episodeGetStatus(episode);
  const avgConfidence = episodeGetAverageConfidence(episode);

  return (
    <React.Fragment>
      <TableRow
        hover
        onClick={() => nav(`/trace/${episode.episode_id}?type=episode`)}
        sx={{ cursor: "pointer" }}
      >
        <TableCell>
          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              setOpen((v) => !v);
            }}
          >
            {open ? <KeyboardArrowDown /> : <KeyboardArrowRight />}
          </IconButton>
        </TableCell>
        <TableCell>
          <Typography
            variant="body2"
            sx={{
              fontFamily: "monospace",
            }}
          >
            {formatDateTime(startTime)}
          </Typography>
        </TableCell>
        <TableCell>
          <Box
            sx={{
              display: "flex",
              flexDirection: "column",
              gap: 0.5,
            }}
          >
            <TypeChip type="episode" />

            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ display: "flex", alignItems: "center", gap: 1 }}
            >
              {/* Trace Count */}
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 0.25,
                }}
              >
                <Layers fontSize="inherit" sx={{ color: "text.disabled" }} />
                {episode.traces.length}
              </Box>

              {/* Priority */}
              <Box sx={{ display: "flex", alignItems: "center", gap: 0.25 }}>
                <Flag
                  fontSize="inherit"
                  sx={{
                    color: getPriorityColor(priority),
                  }}
                />
                {priority}
              </Box>

              {/* Token Usage */}
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 0.25,
                }}
              >
                <Token fontSize="inherit" sx={{ color: "text.disabled" }} />
                {totalTokens}
              </Box>
            </Typography>
          </Box>
        </TableCell>
        <TableCell>
          <StatusChip status={status} />
        </TableCell>
        <TableCell>
          <Typography variant="body2" sx={{ color: "text.disabled" }}>
            —
          </Typography>
        </TableCell>
        <TableCell>
          <Typography
            variant="body2"
            sx={{
              fontFamily: "monospace",
            }}
          >
            {duration}s
          </Typography>
        </TableCell>
        <TableCell>
          <Typography
            variant="body2"
            sx={{
              fontFamily: "monospace",
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
          >
            {episode.episode_id}
          </Typography>
        </TableCell>
        <TableCell>
          <ConfidenceIndicator
            confidence={avgConfidence}
            isAnalyzing={avgConfidence === undefined}
          />
        </TableCell>
      </TableRow>
      <TableRow>
        <TableCell sx={{ p: 0, border: 0 }} colSpan={8}>
          <Collapse in={open} timeout="auto" unmountOnExit>
            <Box sx={{ bgcolor: "action.hover" }}>
              <TraceRows traces={episode.traces} episodeId={episode.episode_id} />
            </Box>
          </Collapse>
        </TableCell>
      </TableRow>
    </React.Fragment>
  );
};

interface EpisodesTableProps {
  episodes: Episode[];
  loading?: boolean;
}

const EpisodesTable: React.FC<EpisodesTableProps> = ({ episodes, loading }) => (
  <Table sx={{ width: "100%", tableLayout: "fixed" }}>
    <TableHead>
      <TableRow
        sx={{
          "& th": {
            fontWeight: 700,
            color: "text.secondary",
            fontSize: "0.75rem",
            textTransform: "uppercase",
            letterSpacing: 0.5,
          },
        }}
      >
        <TableCell sx={{ width: "5%" }} />
        <TableCell sx={{ width: "15%" }}>Timestamp</TableCell>
        <TableCell sx={{ width: "15%" }}>Details</TableCell>
        <TableCell sx={{ width: "13%" }}>Status</TableCell>
        <TableCell sx={{ width: "13%" }}>Error Type</TableCell>
        <TableCell sx={{ width: "10%" }}>Duration</TableCell>
        <TableCell sx={{ width: "15%" }}>Episode ID</TableCell>
        <TableCell sx={{ width: "14%" }}>Average Confidence</TableCell>
      </TableRow>
    </TableHead>
    <TableBody>
      {loading ? (
        Array.from({ length: 10 }).map((_, i) => (
          <TableRow key={i}>
            {Array.from({ length: 8 }).map((_, j) => (
              <TableCell key={j}>
                <Skeleton sx={{ my: 1.75 }} />
              </TableCell>
            ))}
          </TableRow>
        ))
      ) : episodes.length === 0 ? (
        <TableRow>
          <TableCell colSpan={8} align="center" sx={{ py: 6 }}>
            <Typography variant="body2" color="text.disabled">
              No recent activity.
            </Typography>
          </TableCell>
        </TableRow>
      ) : (
        episodes.map((ep) => <EpisodeRow key={ep.episode_id} episode={ep} />)
      )}
    </TableBody>
  </Table>
);

export default EpisodesTable;
