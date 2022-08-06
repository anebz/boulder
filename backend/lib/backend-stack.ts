import * as fs from "fs";
import * as path from "path"
import { Construct } from 'constructs';

import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as events from 'aws-cdk-lib/aws-events';
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as targets from 'aws-cdk-lib/aws-events-targets';
import { PythonFunction } from "@aws-cdk/aws-lambda-python-alpha";

export class BoulderStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // S3 bucket
    const myBucket = new s3.Bucket(this, 'boulder-bucket', {
      bucketName: 'boulderbucket',
      versioned: false,
      publicReadAccess: false,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL
    });

    // Lambda Function
    //const myLambda = new lambda.Function(this, 'BoulderLambda', {
    const myLambda = new PythonFunction(this, 'BoulderLambda', {
      entry: 'lib/lambda',
      index: 'web_scrape.py',
      //code: lambda.Code.fromAsset(path.join(__dirname, 'lambda/web_scrape')),
      handler: 'lambda_handler',
      timeout: cdk.Duration.minutes(9),
      runtime: lambda.Runtime.PYTHON_3_8,
      environment: {
        "S3_BUCKET_NAME": myBucket.bucketName,
        "CSVNAME": "boulderdata.csv",
        "GYMDATANAME": "gymdata.json",
        "OWMAPIKEY": fs.readFileSync(path.join(__dirname, '/../own-api-key.txt'), 'utf8').toString()
      },
    });
    myBucket.grantRead(myLambda);
    myBucket.grantWrite(myLambda);

    // Event for Lambda cron
    const eventRule = new events.Rule(this, 'scheduleRule', {
      schedule: events.Schedule.expression('cron(0/20 5-21 ? * MON-SUN *)')
    });
    eventRule.addTarget(new targets.LambdaFunction(myLambda))
  }
}
