import { Card, CardContent, Box } from '@mui/material';
import Settings from '../components/settings/Settings';

const SettingsPage: React.FC = () => {
    return (
      <Box sx={{ p: 3, height: "100%", display: "flex", flexDirection: "column" }}>
        <Card elevation={0} sx={{ flex: 1, display: "flex", flexDirection: "column"}}>
          <CardContent sx={{ flex: 1, display: "flex", flexDirection: "column", bgcolor: "background.paper", p:0  }}>
            <Settings />
          </CardContent>
        </Card>
      </Box>
    )
}

export default SettingsPage;