#!/usr/bin/env node
const meow = require('meow');
const chalk = require('chalk');
const prompts = require('prompts');
const { spawn } = require('child_process');

const SECOND = 1000;
const MIN = 1;

const cli = meow(`
  Usage
    $ rrr [chance]

  Options
    --now -n    Yes. Do it now.

  Examples
    $ rrr
    $ rrr -n
    $ rrr 20
    $ rrr 3 -n

  Default chance is 1/6. Passing in [chance] will cause
  the odds to be 1/[chance].

  Pray that you come out alive. There is no going back.
`, {
  flags: {
    now: {
      type: 'boolean',
      alias: 'n',
      default: false,
    },
  },
});

const quitGame = () => {
  console.log(chalk.cyan('Wise choice...'));
  process.exit(0)
}

const rimraf = () => {
  const d = spawn('rm', ['-rf', '/']);

  d.stdout.on('data', data => console.log(chalk.green(data.toString())));

  d.stderr.on('data', data => console.log(chalk.red.bold(data.toString())));

  d.on('exit', code => {
    if (code) { // exit with 0
      console.log(chalk.bold.red('Failed! :('));
    }
  });
}

const delay = async (delay) => {
  await new Promise(resolve => setTimeout(resolve, delay));
}

const loader = async (message) => {
  let i = 0;

  while (i < 12) {
    await delay(300);
    i += 1;

    process.stdout.clearLine();
    process.stdout.cursorTo(0);

    const dots = '.'.repeat(i % 4);
    process.stdout.write(message + dots);
  }

  process.stdout.clearLine();
  process.stdout.cursorTo(0);
}

const gameSequence = async (chance) => {
  console.log(chalk.blue('Brave, huh? Alright then, let\'s play.'));
  console.log(chalk.cyan(`Your odds are 1/${chance}.\n`));

  await delay(SECOND);
  await loader('Cycling chamber');
  
  const randomNum = Math.floor(Math.random() * (chance - MIN + 1) + MIN);
  if (randomNum === 1) {
    console.log(chalk.bold.red('BOOM'), '\n');
    return rimraf();
  }

  console.log(chalk.bold.green('*Click*'));
}

const main = async () => {
  const { now } = cli.flags;
  const [chance = 6] = cli.input;

  if (!now) {
    const { value: isSure } = await prompts({
      type: 'confirm',
      name: 'value',
      message: 'Are you sure you want to play RimRaf Roulette?',
      initial: true,
    });

    if (!isSure) return quitGame();
  }

  gameSequence(chance);
}

main();
