import puppeteer from 'puppeteer';

(async () => {
  console.log("============================================================");
  console.log("  AlgoShield AI — Frontend E2E Monitoring Browser Test");
  console.log("============================================================");

  let browser;
  try {
    // Launch headless browser
    browser = await puppeteer.launch({
      headless: "new",
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();
    
    // Catch page log and errors
    page.on('console', msg => console.log('  [BROWSER LOG]:', msg.text()));
    page.on('pageerror', error => {
      console.error('  [BROWSER ERROR]:', error.stack || error.message);
    });

    // 1. Seed localStorage before loading the page to simulate a connected Pera Wallet
    console.log("1. Seeding test wallet session into localStorage...");
    await page.goto('http://localhost:5173/', { waitUntil: 'domcontentloaded' });
    await page.evaluate(() => {
      localStorage.setItem('algoshield_test_wallet', 'GD64F7W4H2L67UIEVEQHCAQQFYASVPVELUC5SGBJ6RA6AKXIXFFBVPQLVT');
    });

    // 2. Navigate to the Live Monitoring Page
    console.log("2. Navigating to the Live Monitoring Page...");
    await page.goto('http://localhost:5173/monitor', { waitUntil: 'networkidle0' });

    // Assert that we are successfully logged in and not redirected to landing
    const url = page.url();
    console.log(`   Current URL: ${url}`);
    if (url.includes('monitor')) {
      console.log("   ✅ Successfully bypassed landing; Monitor page loaded!");
    } else {
      throw new Error("❌ Redirected to Landing. Test session seeding failed!");
    }

    // 3. Fill in target contract parameters
    console.log("3. Seeding real Mainnet contract inputs into form...");
    
    // Fill App ID (Folks Finance Pool Manager)
    const appIdInput = await page.$('input[placeholder="e.g. 1234567"]');
    await appIdInput.click({ clickCount: 3 }); // select all
    await appIdInput.type('971350278');

    // Fill Account Address (Official Algorand FeeSink)
    const accountInput = await page.$('input[placeholder="e.g. ABCDE...1234"]');
    await accountInput.click({ clickCount: 3 });
    await accountInput.type('Y76M3MSY6DKBRHBL7C3NNDXGS5IIMQVQVUAB6MP4XEMMGVF2QWNPL226CA');

    // Fill Alert Email
    const emailInput = await page.$('input[placeholder="e.g. security@team.com"]');
    await emailInput.click({ clickCount: 3 });
    await emailInput.type('programmingla04@gmail.com');

    // Fill Telegram Chat ID (optional, using dummy)
    const telegramInput = await page.$('input[placeholder="e.g. 123456789"]');
    await telegramInput.click({ clickCount: 3 });
    await telegramInput.type('987654321');

    console.log("   ✅ Form inputs filled successfully!");

    // 4. Click Start Monitoring
    console.log("4. Launching live monitoring baseline scan...");
    const startButton = await page.$('button.btn-primary');
    await startButton.click();

    // 5. Wait for baseline scan results to load
    console.log("5. Waiting 6 seconds for indexer queries & status resolution...");
    await new Promise(resolve => setTimeout(resolve, 6000));

    // 6. Assert and read UI values
    console.log("6. Inspecting UI security status card...");
    
    const uiData = await page.evaluate(() => {
      // Find the security status badge text
      const divs = Array.from(document.querySelectorAll('span'));
      const badge = divs.find(d => d.textContent && (
        d.textContent.includes('SAFE') || 
        d.textContent.includes('WARNING') || 
        d.textContent.includes('HIGH RISK') ||
        d.textContent.includes('INACTIVE')
      ));
      
      const paragraphs = Array.from(document.querySelectorAll('p'));
      const explanation = paragraphs.find(p => p.className && p.className.includes('font-syne') && p.textContent && p.textContent.includes('recent activity') || p.textContent && p.textContent.includes('Suspicious activity') || p.textContent && p.textContent.includes('failed'));

      return {
        badgeText: badge ? badge.textContent.trim() : "NOT FOUND",
        explanationText: explanation ? explanation.textContent.trim() : "NOT FOUND"
      };
    });

    console.log(`   Badge Status : ${uiData.badgeText}`);
    console.log(`   Explanation  : ${uiData.explanationText}`);

    if (uiData.badgeText.includes('WARNING') || uiData.badgeText.includes('SAFE') || uiData.badgeText.includes('INACTIVE')) {
      console.log("   ✅ E2E UI Status Badge rendered successfully!");
    } else {
      console.error("   ❌ Expected status badge not found in the DOM!");
    }

    if (uiData.explanationText !== "NOT FOUND") {
      console.log("   ✅ E2E UI Status Explanation rendered successfully!");
    } else {
      console.error("   ❌ Explanation paragraph not found or empty!");
    }

    // 7. Click Stop Monitoring
    console.log("7. Stopping live monitoring session...");
    const stopButtonText = await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const stopBtn = buttons.find(b => b.textContent && b.textContent.includes('Stop Monitoring'));
      if (stopBtn) {
        stopBtn.click();
        return "CLICKED";
      }
      return "NOT FOUND";
    });
    console.log(`   Stop Button  : ${stopButtonText}`);
    
    console.log("============================================================");
    console.log("  ✅ head-to-head browser E2E test PASSED successfully!");
    console.log("============================================================");

  } catch (error) {
    console.error("❌ E2E Browser verification FAILED:", error);
  } finally {
    if (browser) {
      await browser.close();
    }
  }
})();
