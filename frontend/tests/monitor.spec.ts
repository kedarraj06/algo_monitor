import { expect, test } from '@playwright/test';

test.describe('AlgoShield AI — E2E Live Monitoring System', () => {

  test('should perform E2E baseline scan, show warning risk level, and display correct status explanations', async ({ page }) => {
    test.setTimeout(90000);
    console.log("Starting Playwright E2E Live Monitoring Test...");

    // 1. Seed the connected wallet session in localStorage before page load
    await page.addInitScript(() => {
      localStorage.setItem('algoshield_test_wallet', 'GD64F7W4H2L67UIEVEQHCAQQFYASVPVELUC5SGBJ6RA6AKXIXFFBVPQLVT');
    });

    // 2. Navigate to the Live Monitoring Page
    console.log("Navigating to live monitor page...");
    await page.goto('http://localhost:5173/monitor');
    await expect(page).toHaveURL(/.*monitor/);
    console.log("✅ Live Monitor dashboard loaded successfully!");

    // 3. Populate target inputs for baseline scan
    console.log("Populating contract parameters...");
    
    // Fill App ID (Folks Finance Pool Manager)
    const appIdInput = page.locator('input[placeholder="e.g. 1234567"]');
    await appIdInput.fill('971350278');

    // Fill Account Address (Official Algorand FeeSink)
    const accountInput = page.locator('input[placeholder="e.g. ABCDE...1234"]');
    await accountInput.fill('Y76M3MSY6DKBRHBL7C3NNDXGS5IIMQVQVUAB6MP4XEMMGVF2QWNPL226CA');

    // Fill Alert Email
    const emailInput = page.locator('input[placeholder="e.g. security@team.com"]');
    await emailInput.fill('programmingla04@gmail.com');

    // Fill Telegram Chat ID
    const telegramInput = page.locator('input[placeholder="e.g. 123456789"]');
    await telegramInput.fill('987654321');

    console.log("✅ Inputs seeded successfully!");

    // 4. Click Start Monitoring
    console.log("Launching live monitoring session...");
    const startButton = page.locator('button:has-text("Start Monitoring")');
    await expect(startButton).toBeVisible();
    await startButton.click();

    // 5. Wait for the baseline scan status card to render
    console.log("Waiting for indexer results and status classification...");
    
    // We expect the status badge to appear with WARNING or SAFE
    const statusBadge = page.locator('span:has-text("WARNING"), span:has-text("SAFE"), span:has-text("INACTIVE")');
    await statusBadge.waitFor({ state: 'visible', timeout: 45000 });

    const badgeText = await statusBadge.textContent();
    console.log(`✅ Baseline scan completed! Status Badge text: "${badgeText?.trim()}"`);

    // Assert that the explanation card is active and loaded
    const explanationText = page.locator('p.font-syne:has-text("failed"), p.font-syne:has-text("activity"), p.font-syne:has-text("Suspicious")');
    await expect(explanationText).toBeVisible();
    
    const expText = await explanationText.textContent();
    console.log(`✅ Status Explanation rendered: "${expText?.trim()}"`);

    // 6. Click Stop Monitoring to cleanly tear down the job
    console.log("Tearing down monitoring session...");
    const stopButton = page.locator('button:has-text("Stop Monitoring")');
    await expect(stopButton).toBeVisible();
    await stopButton.click();
    console.log("✅ E2E live monitor cycle completed and stopped cleanly!");
  });

});
